#!/usr/bin/env python

import argparse
import random
import sys

from db import *
from storm.locals import *


DEFAULT_DB = 'gen/itunes.db'


def sample(dbname, usernames, k):
    store = Store(create_database('sqlite:%s' % dbname))
    tracks = list()
    for user in store.find(User):
        if user.name in usernames:
            tracks.extend(user.tracks)
    return random.sample(tracks, k)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('users', nargs='+', type=unicode)
    parser.add_argument('size', type=int)
    parser.add_argument('--db', default=DEFAULT_DB)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    for track in sample(args.db, args.users, args.size):
        print "%s - %s" % (track.artist.encode('utf-8'),
                track.title.encode('utf-8'))
