#!/usr/bin/env python
"""Fetch tags on Last.fm for new tracks.

This script listens to the message queue for new tracks in the system for which
we don't have the tags yet. It respects the Last.fm API rate limits.
"""

import argparse
import json
import pika
import liblfm
import libunison.utils as uutils
import logging
import time
import threading

from libunison.models import Track


DEFAULT_RATE = 1.0  # Maximal number of items processed every second.
CONFIG = uutils.get_config()


class Fetcher(threading.Thread):
    """Last.fm track tags fetcher.

    Listens for jobs on the message queue, and processes them sequentially at a
    given rate (in order to respect the Last.fm API rate limits).
    """

    def __init__(self, rate, lfm, store, logger):
        self._rate = rate
        self._lfm = lfm
        self._store = store
        self._logger = logger
        self._conn = None
        threading.Thread.__init__(self)

    def run(self):
        """Start listening to messages from the queue."""
        host = CONFIG['queue']['host']
        queue = CONFIG['queue']['name']
        self._conn = pika.BlockingConnection(pika.ConnectionParameters(host))
        self._logger.info("sucessfully connected to host '%s'" % host)
        channel = self._conn.channel()
        # Creates the queue if it doesn't exist yet.
        channel.queue_declare(queue=queue, durable=True)
        # Process items from the queue. We ack them immediately.
        self._logger.info("start listening on queue '%s'..." % queue)
        channel.basic_consume(self._process, queue=queue)
        channel.start_consuming()

    def close(self):
        """Close the connection to RabbitMQ."""
        self._logger.info('closing the connection')
        self._conn.close()

    def _process(self, channel, method, properties, body):
        """Process a message from the queue.

        Route the message to the correct function depending on the action.
        """
        channel.basic_ack(delivery_tag=method.delivery_tag)
        message = json.loads(body)
        if message['action'] == 'track-tags':
            self._track_tags(message['track'])
        elif message['action'] == 'track-info':
            self._track_info(message['track'])
        # Wait for a while (implements the rate limiting).
        time.sleep(1.0 / self._rate)

    def _track_tags(self, meta):
        track = self._store.find(Track, (Track.artist == meta['artist'])
                & (Track.title == meta['title'])).one()
        if track is None:
            self._logger.warn("track not in database: %r" % meta)
            return
        try:
            tags = self._lfm.top_tags(track.artist, track.title)
        except Exception as ex:
            if type(ex) is LookupError and ex.args[0] == 'Track not found':
                # Track not found => no tags.
                self._logger.info("track not found on Last.fm: %r" % meta)
                self._store_tags(track, [])
            else:
                self._logger.error("couldn't fetch tags for: %r (%r)"
                        % (meta, ex))
        else:
            features = uutils.track_features(tags)
            self._store_tags(track, tags, features)
            self._logger.info("fetched tags for track: %r" % meta)

    def _store_tags(self, track, tags, features=None):
        """Store a track's tags in the database."""
        track.tags = json.dumps(tags).decode('utf-8')
        if features is not None:
            track.features = uutils.encode_features(features)
        self._store.commit()

    def _track_info(self, meta):
        track = self._store.find(Track, (Track.artist == meta['artist'])
                & (Track.title == meta['title'])).one()
        if track is None:
            self._logger.warn("track not in database: %r" % meta)
            return
        try:
            info = self._lfm.track_info(track.artist, track.title)
        except Exception as ex:
            self._logger.warn("couldn't fetch infos for: %r (%r)"
                    % (meta, ex))
        else:
            track.image = info['image']
            track.listeners = info['listeners']
            self._store.commit()
            self._logger.info("fetched track info for: %r" % meta)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rate', type=float, default=DEFAULT_RATE)
    return parser.parse_args()


def _get_logger():
    formatter = logging.Formatter('%(asctime)s: %(levelname)s - %(message)s')
    handler = logging.StreamHandler()  # Log to stderr.
    handler.setFormatter(formatter)
    logger = logging.getLogger('tagfetcher')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger


if __name__ == '__main__':
    args = _parse_args()
    logger = _get_logger()
    for key in [CONFIG['lastfm']['key']] + CONFIG['lastfm']['addkeys']:
        lfm = liblfm.LastFM(key)
        store = uutils.get_store(CONFIG['database']['string'])
        fetcher = Fetcher(args.rate, lfm, store, logger)
        # Launch the fetcher !
        fetcher.start()
