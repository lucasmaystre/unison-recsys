#!/usr/bin/env python
"""Compute the similarity between two tracks.

Currently, the similarity measure used is the cosine measure, i.e. the dot
product of the normalized track vectors.
"""

import argparse
import json
import sqlite3
import struct

from math import log, log1p, sqrt
from util import (DB_PATH, TAGS_PATH, WEIGHTS_PATH,
        get_vector, print_vector, print_track, load_tags, load_weights)


def similarity(t1, t2, db, weight_fct):
    conn = sqlite3.connect(db)
    v1 = compute_vector(t1, weight_fct, conn)
    v2 = compute_vector(t2, weight_fct, conn)
    # Cosine similarity (= dot product, vectors are normalized).
    return sum([v1[i] * v2[i] for i in range(len(v1))])


def compute_vector(track, weight_fct, db_conn):
    dim = len(get_vector(db_conn, 'rock'))  # TODO temp.
    vector = [0] * dim
    for tag, count in track['tags']:
        curr = get_vector(db_conn, tag)
        if curr is None:
            # TODO Not very elegant.
            print "Tag %s not in database." % tag
            continue
        weight = weight_fct(tag) * log1p(float(count)) / log(2)
        vector = [(weight*x + y) for x, y in zip(curr, vector)]
    norm = sqrt(sum([x*x for x in vector]))
    if norm > 0:
        return tuple([x / norm for x in vector])
    else:
        return tuple(vector)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('track1', type=open)
    parser.add_argument('track2', type=open)
    parser.add_argument('--db', default=DB_PATH)
    parser.add_argument('--weights', default=WEIGHTS_PATH)
    parser.add_argument('--tags', default=TAGS_PATH)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    t1 = json.loads(args.track1.read())
    t2 = json.loads(args.track2.read())
    print('-------- Track 1')
    print_track(t1)
    print('-------- Track 2')
    print_track(t2)
    weights = load_weights(args.weights)
    tags = load_tags(args.tags)
    weight_fct = lambda tag: weights[tags[tag]]
    print similarity(t1, t2, args.db, weight_fct)
