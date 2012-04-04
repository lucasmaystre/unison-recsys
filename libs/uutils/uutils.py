#!/usr/bin/env python
"""Utilities for the Unison recommender system."""

import marshal
import math
import os
import os.path
import struct


GEN_ROOT = './gen'
TAGS_PATH = '%s/tags.marshal' % GEN_ROOT
MATRIX_PATH = '%s/tag-track.mat' % GEN_ROOT
UT_PATH = '%s/result-Ut' % GEN_ROOT
DB_PATH = '%s/tags.db' % GEN_ROOT
WEIGHTS_PATH = '%s/weights.marshal' % GEN_ROOT

QUERY_SELECT = "SELECT vector, weight FROM tags WHERE name = ?"


def _load(path):
    """Read a marshalled structure from disk."""
    f = open(path, 'rb')
    return marshal.load(f)


def _dump(data, path):
    """Write a marshalled structure to disk."""
    create_tree(path)
    f = open(path, 'wb')
    marshal.dump(data, f)


def create_tree(path):
    """Recursively create a directory structure.

    Useful when attempting to write to a file that is in a folder hierarchy that
    does not necessarily exist yet.

    Beware, there's a small race condition between the execution of
    os.path.exists() and os.makedirs().
    """
    path = os.path.abspath(path)
    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        os.makedirs(folder)


def dump_tags(tags_dict, path=TAGS_PATH):
    _dump(tags_dict, path)


def load_tags(path=TAGS_PATH):
    return _load(path)


def dump_weights(weights, path=WEIGHTS_PATH):
    _dump(weights, path)


def load_weights(path=WEIGHTS_PATH):
    return _load(path)


def get_vector(conn, tag):
    """Read a feature vector from the database.

    Small helper function that takes:
        conn - a connection to a SQLite database
        tag  - the name of a tag
    and returns the feature vector associated with the tag (or None if the tag
    wasn't found in the database).
    """
    res = conn.execute(QUERY_SELECT, (tag,)).fetchone()
    if res is None:
        return None, None
    raw, weight = res
    vector = list()
    for i in xrange(0, len(raw), 4):
        val, = struct.unpack('!f', raw[i:i+4])
        vector.append(val)
    norm = math.sqrt(sum([x*x for x in vector]))
    if norm > 0:
        return tuple([x / norm for x in vector]), weight
    else:
        return tuple(vector), weight


def get_dimensions(conn):
    res = conn.execute("SELECT vector FROM tags LIMIT 1").fetchone()
    return len(res[0]) / 4


def print_vector(vector, weight=None):
    """Pretty print a feature vector."""
    print tuple([('%.2f' % x) for x in vector])
    print "l2-norm: %.2f" % math.sqrt(sum([x*x for x in vector]))
    if weight is not None:
        print "weight: %.2f" % weight


def print_track(track):
    """Pretty print track information (in last.fm MSD format)."""
    print "Artist: %s" % track.get('artist', '<unkown>')
    print "Title:  %s" % track.get('title', '<unknown>')
    print "Tags:   %d" % len(track.get('tags', []))
    for tag in track.get('tags', []):
        print "- %s (%s)" % tuple(tag)
