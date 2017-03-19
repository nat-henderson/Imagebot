# Imagebot
Got some recurring irritating video to process?  Got a slack channel?  This solves your dumb problem.

## The actual problem this solves

We have a set of Piper cameras.  Piper is one of those IoT security systems where it'll just notify you on a phone or something if it detects something.  They've got a handful of ways to detect things: noise, movement, IR, and I think a few other things we never bothered to hook up.

We have a Slack channel for our house.  Piper integrates with IFTTT, so we have Slack notifications from our security cameras when something goes wrong.  It posts a video to the channel, which is pretty handy, actually.

We have a Roomba.  The Roomba trips the motion detector every day.  Usually a couple times!  And you know how it is with false-positives; you see a bunch of them and the true positives get lost in the noise.  The videos being posted to the channel started getting ignored, which makes the whole setup not that useful.

I work at Google in Research and Machine Intelligence.  Computers are really good at repetitive boring-ass tasks, and recognizing whether a video contains a Roomba is totally repetitive and boring.

## Setup

Dumb-ass-problem = Dumb-ass-solution.

Oughtta be that all you have to do is copy `Dockerfile.example` to `Dockerfile`, then replace the bunch of tags with your assorted keys and client ids and secrets and whatnot.

Then you fire it up with `docker run` just like everything else that uses Docker.

It's going to respond to any URL that starts with ift.tt in your channel [that's stupid; just sort of happens to work in this case], with an image from ~10s into the video, then tries to categorize it.

## Troubleshooting

Haha, why are you looking at this section; I'm the guy who made the shitty robot respond to urls that start with 'ift.tt'; what kind of testing do you think I set up here?
