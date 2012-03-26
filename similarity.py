#!/usr/bin/env python
"""Compute the similarity between two tracks.

Currently, the similarity measure used is the cosine measure, i.e. the dot
product of the normalized track vectors.
"""

import argparse
import math
import sqlite3
import struct

QUERY_SELECT = "SELECT vector FROM tags WHERE name = ?"


def similarity(t1, t2, db):
    conn = sqlite3.connect(db)
    tag = dict()
    for name, val in (t1 + t2):
        res = conn.execute(QUERY_SELECT, (name,)).fetchone()
        if res is None:
            raise Exception("Tag '%s' was not found in the database." % name)
        tag[name] = list()
        raw = res[0]
        for i in xrange(0, len(raw), 4):
            component, = struct.unpack('!f', raw[i:i+4])
            tag[name].append(component)
    v1 = compute_vector(t1, tag)
    v2 = compute_vector(t2, tag)
    # Cosine similarity (= dot product, vectors are normalized).
    return sum([v1[i] * v2[i] for i in range(len(v1))])


def compute_vector(track, tag):
    # Figure out the dimensionality.
    dim = len(tag.itervalues().next())
    vector = [0] * dim
    # Add the weighted values for each tag.
    for name, val in track:
        vector = [(val*x + y) for x, y in zip(tag[name], vector)]
    # Normalize.
    norm = math.sqrt(sum([x*x for x in vector]))
    return tuple([x / norm for x in vector])
    

def track_info(info):
    # Treat it as Unicode, and discard the case.
    decoded = unicode(info, encoding='utf-8').lower()
    elems = decoded.split(',')
    tags = list()
    for elem in elems:
        values = elem.split('=')
        if len(values) == 2:
            tags.append((values[0], float(values[1])))
        else:
            tags.append((values[0], 100.0))
    return tuple(tags)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('t1', type=track_info)
    parser.add_argument('t2', type=track_info)
    parser.add_argument('--db', required=True)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    try:
        print similarity(args.t1, args.t2, args.db)
    except Exception as e:
        print e
