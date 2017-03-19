import os
from slackclient import SlackClient
import websocket
import logging
import json
import requests
import tempfile
import re
import subprocess
from imgurpython import ImgurClient
import is_stealer
from google.cloud import storage

logging.basicConfig(level=logging.DEBUG)

slack_token = os.environ['SLACK_API_TOKEN']
sc = SlackClient(slack_token)
imgur_client = ImgurClient(os.environ['IMGUR_CLIENT_ID'],
                           os.environ['IMGUR_CLIENT_SECRET'])
PROJECT_NAME = 'spoopbot-156709'
storage_client = storage.Client(project=PROJECT_NAME)
BUCKET_NAME = 'spoopbot-example-mp4s'
example_bucket = storage_client.get_bucket(BUCKET_NAME)
LOCAL_EXAMPLES_DIR = '/examples/'
MOST_RECENT_URL = None

rtm_start = sc.api_call('rtm.start',
        simple_latest=True)

def download_examples():
    count = 0
    for example in example_bucket.list_blobs():
        if not '.mp4' in example.name:
            continue
        local_fname = os.path.join(LOCAL_EXAMPLES_DIR, example.name.rstrip('/'))
        if not os.path.exists(os.path.dirname(local_fname)):
            os.makedirs(os.path.dirname(local_fname))
        with open(local_fname, 'w') as f:
            example.download_to_file(f)
        subprocess.check_call(['avconv', '-i', local_fname,
            '-f', 'image2', os.path.join(os.path.dirname(local_fname),
                os.path.splitext(os.path.basename(local_fname))[0] + '-%03d.jpg')])
        os.remove(local_fname)
        count += 1
    return count

def download_model():
    for example in example_bucket.list_blobs():
        if not 'retrained_' in example.name:
            continue
        local_fname = os.path.join('./', os.path.basename(example.name))
        with open(local_fname, 'w') as f:
            example.download_to_file(f)

def retrain():
    output = subprocess.check_output(['python', '/tensorflow/tensorflow/examples/image_retraining/retrain.py',
        '--bottleneck_dir=/tf_files/bottlenecks', '--how_many_training_steps', '1000',
        '--model_dir=/tf_files/inception', '--output_graph=/tmp/retrained_graph.pb',
        '--output_labels=/tf_files/retrained_labels.txt', '--image_dir',
        LOCAL_EXAMPLES_DIR],
        stderr=subprocess.STDOUT)

def upload_example(example, classification):
    blob = storage.Blob(os.path.join(classification, os.path.basename(example)), example_bucket)
    with open(example, 'rb') as f:
        blob.upload_from_file(f)

def upload_model():
    blob = storage.Blob('retrained_graph.pb', example_bucket)
    with open('/tf_files/retrained_graph.pb', 'rb') as f:
        blob.upload_from_file(f)

    blob = storage.Blob('retrained_labels.txt', example_bucket)
    with open('/tf_files/retrained_labels.txt', 'rb') as f:
        blob.upload_from_file(f)

def download_file(url, local_filename):
    # NOTE the stream=True parameter
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

def on_message(ws, message):
    message = json.loads(message)
    if not 'type' in message or message['type'] != 'message':
        print 'not a message.'
        return
    text = ''
    if 'text' in message:
        text = message['text']
    if 'attachments' in message:
        atts = message['attachments']
        print atts
        text = text + '\n'.join(att.get('pretext', '') + ' ' + att.get('text', '') for att in atts)
    if not text.strip():
        print 'no text to read.'
        return
    print text
    if 'ift.tt' in text:
        spoopbot_url(text)
    elif text.startswith('imagebot'):
        if 'imagebot retrain' in text:
            sc.api_call(
                    'chat.postMessage',
                    channel='#-funsafe-house',
                    text='Sure thing, buddy; retraining myself on the accumulated examples.',
                    as_user=True)
            count = download_examples()
            sc.api_call(
                    'chat.postMessage',
                    channel='#-funsafe-house',
                    text='I found a total of %d examples to train on.  Thiiiiis might take a bit.' % count,
                    as_user=True)
            retrain()
            sc.api_call(
                    'chat.postMessage',
                    channel='#-funsafe-house',
                    text='Ooooookay, retraining done!',
                    as_user=True)
            upload_model()
            download_model()
        else:
            if MOST_RECENT_URL is None:
                sc.api_call(
                        'chat.postMessage',
                        channel='#-funsafe-house',
                        text='I have not seen a URL recently, sorry!',
                        as_user=True)
                return
            cls = text.split(' ')[-1]
            sc.api_call(
                    'chat.postMessage',
                    channel='#-funsafe-house',
                    text='Okay sure!  I will mark the most recent URL as %s.' % cls,
                    as_user=True)
            fname = tempfile.mktemp(suffix='.mp4')
            download_file(MOST_RECENT_URL, fname)
            upload_example(fname, cls)


def spoopbot_url(text):
    sc.api_call(
            'chat.postMessage',
            channel='#-funsafe-house',
            text='I saw that spoopbot url, lemme check on it.',
            as_user=True)

    tmp_filename = tempfile.mktemp() + '.mp4'
    output_file = tempfile.mktemp() + '.jpg'
    bad_re = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    url = re.search(bad_re, text).group(0).rstrip('>')
    global MOST_RECENT_URL
    MOST_RECENT_URL = url
    try:
        download_file(url, tmp_filename)
        subprocess.check_call(['avconv', '-ss', '10', '-i', tmp_filename,
            '-frames', '1', '-f', 'image2', output_file])
        imgur_url = imgur_client.upload_from_path(output_file)
        classes = is_stealer.what_class(output_file)
        print imgur_url['link']
        sc.api_call(
                'chat.postMessage',
                channel='#-funsafe-house',
                text=imgur_url['link'] + '\n' + classes,
                as_user=True)
    finally:
        if os.path.isfile(tmp_filename):
            os.remove(tmp_filename)
        if os.path.isfile(output_file):
            os.remove(output_file)


if __name__ == '__main__':
    download_model()
    ws = websocket.WebSocketApp(rtm_start['url'], on_message=on_message)
    ws.run_forever()

