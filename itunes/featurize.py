#!/usr/bin/env python

import argparse
import json
import libunison.utils as uutils

from db import *
from storm.expr import Eq, Ne


DEFAULT_DB = 'gen/itunes.db'


def fill_features(store):
    conn = uutils.get_feature_db()
    @uutils.memo
    def tag_fct(tag):
        return uutils.tag_features(tag, conn=conn, normalize=True)
    for track in store.find(Track, Ne(Track.tags, None)
            & Eq(Track.features, None)):
        print "Processing %s - %s ..." % (track.artist, track.title)
        if isinstance(track.tags, basestring):
            continue
        features = uutils.track_features(
                track.tags, conn=conn, tag_fct=tag_fct)
        if features is None:
            # The track probably didn't have any tags.
            print "-- Feature vector is null."
            continue
        # Serialize and save the feature vector.
        track.features = uutils.encode_features(features)
        store.commit()


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=DEFAULT_DB)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    store = Store(create_database('sqlite:%s' % args.db))
    fill_features(store)
