#!/usr/bin/env python
"""Convert features to the format used by LIBSVM.

This simple script transforms a file as output by ./classifier.py genfeat into
the format used by the LIBSVM command line tools.
"""

import argparse
import struct


DEFAULT_DIM = 50
STRUCT_FLOAT = struct.Struct('!f')


def decode(encoded):
    features = list()
    for i in xrange(0, len(encoded), 8):
        raw = encoded[i:i+8].decode('hex_codec')
        features.append(STRUCT_FLOAT.unpack(raw)[0])
    return features


def parse(features, dim):
    items = list()
    for line in open(features):
        status, encoded = line.strip().split('|')
        item = decode(encoded)[:dim]
        label = 0 if status == 'banned' else 1
        items.append((item, label))
    return items


def write(items):
    for item, label in items:
        line = "%d" % label
        for i, val in enumerate(item, start=1):
            line += " %d:%f" % (i, val)
        print line


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file')
    parser.add_argument('--dimensions', type=int, default=DEFAULT_DIM)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    items = parse(args.file, args.dimensions)
    write(items)
