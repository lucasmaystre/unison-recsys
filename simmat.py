#!/usr/bin/env python
"""Compute a similarity matrix from track metadata.

This is pretty messy. Whatever.
"""

import json
import os
import os.path
import similarity
import sqlite3
import sys

ROOT_DIR = 'gen/metadata'
DATABASE = 'd70.db'

def w(s):
    sys.stdout.write(s)

if __name__ == '__main__':
    conn = sqlite3.connect(DATABASE)
    files = os.listdir(ROOT_DIR)[15:30]
    nb = len(files)
    for x in xrange(nb):
        f = open(os.path.join(ROOT_DIR, files[x]))
        count = len(json.loads(f.read())['tags'])
        print "%-3d - %s (%d tags)" % (x, files[x], count) 
    w("\n\n")
    # Print the matrix.
    w("   ")
    for x in xrange(nb):
        w("  %5d" % x)
    w("\n")
    for x in xrange(nb):
        w("%3d" % x)
        fx = open(os.path.join(ROOT_DIR, files[x]))
        tx = json.loads(fx.read())
        for y in xrange(nb):
            fy = open(os.path.join(ROOT_DIR, files[y]))
            ty = json.loads(fy.read())
            sim = similarity.similarity(tx, ty, conn)
            w("  %5.2f" % sim)
        w("\n")
