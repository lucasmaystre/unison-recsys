#!/usr/bin/env python
"""Send an arbitrary message to the queue."""

import libunison.utils as uutils
import pika
import sys


CONFIG = uutils.get_config()
DEFAULT_MESSAGE = '{"title":"Pjanoo", "artist":"Eric Prydz"}'


if __name__ == '__main__':
    host = CONFIG['queue']['host']
    queue = CONFIG['queue']['name']
    # Set up the connection.
    conn = pika.BlockingConnection(pika.ConnectionParameters(host))
    channel = conn.channel()
    # Creates the queue if it doesn't exist yet.
    channel.queue_declare(queue=queue, durable=True)
    # Send a message to the queue.
    if len(sys.argv) > 1:
        message = sys.argv[1]
    else:
        message = DEFAULT_MESSAGE
    channel.basic_publish(exchange='', routing_key='lastfm', body=message,
            properties=pika.BasicProperties(delivery_mode=2))
    print "Sent message %r" % message
    # Closing the connection flushes all the messages.
    conn.close()
