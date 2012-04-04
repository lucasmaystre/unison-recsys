#!/usr/bin/env python
"""Read tag feature vectors from the database."""

import argparse
import math
import sqlite3
import struct
import sys

from uutils import DB_PATH, get_vector, print_vector


def _parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tag')
    parser.add_argument('--db', default=DB_PATH)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    # Convert tag name to UTF-8 and discard case.
    tag = unicode(args.tag, encoding='utf-8').lower()
    conn = sqlite3.connect(args.db)
    vector, weight = get_vector(conn, tag)
    if vector is None:
        print "Tag not found."
        sys.exit(0)
    print_vector(vector, weight)
