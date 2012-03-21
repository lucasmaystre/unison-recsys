#!/usr/bin/env python
"""Read tag feature vectors from the database."""

import argparse
import sqlite3
import struct
import sys


QUERY_SELECT = "SELECT vector FROM tags WHERE name = ?"


def get_features(db, tag):
    conn = sqlite3.connect(db)
    res = conn.execute(QUERY_SELECT, (tag,)).fetchone()
    if res is None:
        return None
    raw = res[0]
    vector = list()
    for i in xrange(0, len(raw), 4):
        val, = struct.unpack('!f', raw[i:i+4])
        vector.append(val)
    return vector


def pretty_print(vector):
    print tuple([('%.2f' % x) for x in vector])


def _parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tag')
    parser.add_argument('--db', required=True)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    # Convert tag name to UTF-8.
    tag = unicode(args.tag, encoding='utf-8')
    vector = get_features(args.db, tag)
    if vector is None:
        print "Tag not found."
        sys.exit(0)
    pretty_print(vector)
