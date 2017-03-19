import tensorflow as tf
import sys

label_lines = [line.rstrip() for line in tf.gfile.GFile('retrained_labels.txt')]
with tf.gfile.FastGFile('retrained_graph.pb', 'rb') as f:
  graph_def = tf.GraphDef()
  graph_def.ParseFromString(f.read())
  _ = tf.import_graph_def(graph_def, name='')

def what_class(image_path):
  print image_path
  image_data = tf.gfile.FastGFile(image_path, 'rb').read()

  with tf.Session() as sess:
    softmax_tensor = sess.graph.get_tensor_by_name('final_result:0')
    predictions = sess.run(softmax_tensor, {'DecodeJpeg/contents:0': image_data})
    top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]

    classes = []
    for node_id in top_k:
      name = label_lines[node_id]
      score = predictions[0][node_id]
      classes.append('%s (score = %.5f)' % (name, score))
    print '\n'.join(classes)
    return '\n'.join(classes)
