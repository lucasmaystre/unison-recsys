#!/usr/bin/env python
"""Simple utility to display track information given an MSD track ID."""

import argparse
import json

from util import print_track


DATASET_ROOT = './data/lastfm_raw'


def tid(string):
    if len(string) != 18 or string != string.upper() or string[:2] != 'TR':
        raise argparse.ArgumentTypeError('invalid tid')
    return string


def _parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--folder', default=DATASET_ROOT)
    parser.add_argument('tid', type=tid)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    path = '%s/%s/%s/%s/%s.json' % (args.folder, args.tid[2], args.tid[3],
            args.tid[4], args.tid)
    try:
        data = open(path).read()
    except IOError:
        # We probably don't know this tid.
        print "Could not find specified tid (%s)." % tid
        sys.exit(0)
    print_track(json.loads(data))
