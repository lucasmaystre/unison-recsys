#!/usr/bin/env python
"""Send an arbitrary message to the queue."""

import argparse
import libunison.utils as uutils
import pika
import sys


CONFIG = uutils.get_config()
ACTION_TAGS = 'track-tags'
ACTION_INFO = 'track-info'
MESSAGE_FORMAT = '{"action": "%s", "track": %s}'
DEFAULT_TRACK = '{"title":"Pjanoo", "artist":"Eric Prydz"}'


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', default=ACTION_TAGS,
            choices=[ACTION_TAGS, ACTION_INFO])
    parser.add_argument('track', nargs='?', default=DEFAULT_TRACK)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    host = CONFIG['queue']['host']
    queue = CONFIG['queue']['name']
    # Set up the connection.
    conn = pika.BlockingConnection(pika.ConnectionParameters(host))
    channel = conn.channel()
    # Creates the queue if it doesn't exist yet.
    channel.queue_declare(queue=queue, durable=True)
    # Send a message to the queue.
    message = MESSAGE_FORMAT % (args.action, args.track)
    channel.basic_publish(exchange='', routing_key='lastfm', body=message,
            properties=pika.BasicProperties(delivery_mode=2))
    print "Sent message %r" % message
    # Closing the connection flushes all the messages.
    conn.close()
