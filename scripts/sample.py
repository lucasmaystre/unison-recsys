#!/usr/bin/env python
"""Uniformly distributed random sample of lines in a file."""

import argparse
import random
import sys


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('ratio', type=float)
    parser.add_argument('file')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    lines = open(args.file).readlines()
    size = int(args.ratio * len(lines))
    for sample in random.sample(lines, size):
        sys.stdout.write(sample)
