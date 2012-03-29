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
        get_dimensions, get_vector, print_vector, print_track)


def similarity(t1, t2, db_conn):
    v1 = compute_vector(t1, db_conn)
    v2 = compute_vector(t2, db_conn)
    # Cosine similarity (= dot product, vectors are normalized).
    return sum([v1[i] * v2[i] for i in range(len(v1))])


def compute_vector(track, db_conn):
    vector = [0] * get_dimensions(db_conn)
    for tag, count in track['tags']:
        curr, gw = get_vector(db_conn, tag)
        if curr is None:
            continue
        weight = gw * log1p(float(count)) / log(2)
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
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    t1 = json.loads(args.track1.read())
    t2 = json.loads(args.track2.read())
    print('-------- Track 1')
    print_track(t1)
    print('-------- Track 2')
    print_track(t2)
    db_conn = sqlite3.connect(args.db)
    print similarity(t1, t2, db_conn)
