#!/usr/bin/env python

import argparse
import liblfm
import libunison.utils as uutils
import time

from db import *
from storm.expr import Eq


DEFAULT_DB = 'gen/itunes.db'
CONFIG = uutils.get_config()


def get_tags(store):
    lfm = liblfm.LastFM(CONFIG['lastfm']['key'])
    for track in store.find(Track, Eq(Track.tags, None)):
        print "Processing %s - %s ..." % (track.artist, track.title)
        try:
            track.tags = lfm.top_tags(track.artist, track.title)
        except LookupError as e:
            print "--- %s" % repr(e)
            continue
        except:
            print "WTF ??? %s" % repr(e)
        store.commit()
        time.sleep(1.0)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=DEFAULT_DB)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    store = Store(create_database('sqlite:%s' % args.db))
    get_tags(store)
