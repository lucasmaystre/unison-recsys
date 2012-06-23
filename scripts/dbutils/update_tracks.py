#!/usr/bin/env python

import argparse
import datetime
import json
import libunison.utils as uutils
import pika
import time

from libunison.models import Track
from storm.locals import *


CONFIG = uutils.get_config()


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('interval', type=int)
    return parser.parse_args()


def init_track(track):
    """Initialize a new track.

    To be used when creating a new track. In concrete terms, this function
    generates and sends the jobs that will fetch the track's tags and other
    information.
    """
    meta = {'artist': track.artist, 'title': track.title}
    tags_msg = json.dumps({
      'action': 'track-tags',
      'track': meta,
    })
    info_msg = json.dumps({
      'action': 'track-info',
      'track': meta,
    })
    # Set up the connection.
    queue = CONFIG['queue']['name']
    conn = pika.BlockingConnection(
            pika.ConnectionParameters(CONFIG['queue']['host']))
    channel = conn.channel()
    # Creates the queue if it doesn't exist yet.
    channel.queue_declare(queue=queue, durable=True)
    # Send the messages to the queue.
    channel.basic_publish(exchange='', routing_key=queue, body=tags_msg,
            properties=pika.BasicProperties(delivery_mode=2))
    channel.basic_publish(exchange='', routing_key=queue, body=info_msg,
            properties=pika.BasicProperties(delivery_mode=2))
    # Closing the connection flushes all the messages.
    conn.close()


if __name__ == '__main__':
    args = _parse_args()
    threshold = datetime.datetime.fromtimestamp(
            time.time() - args.interval * 60 * 60)
    store = uutils.get_store()
    for track in store.find(Track,
            (Track.tags == None) & (Track.updated < threshold)):
        init_track(track)
        print "%s - %s" % (track.artist, track.title)
