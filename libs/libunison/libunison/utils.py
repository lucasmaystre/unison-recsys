#!/usr/bin/env python
"""Utilities for the Unison recommender system."""

import base64
import marshal
import math
import os
import os.path
import struct
import yaml
import sqlite3
import storm.locals

from functools import wraps
from math import log, log1p


GEN_ROOT = './gen'
TAGS_PATH = '%s/tags.marshal' % GEN_ROOT
MATRIX_PATH = '%s/tag-track.mat' % GEN_ROOT
UT_PATH = '%s/result-Ut' % GEN_ROOT
DB_PATH = '%s/tags.db' % GEN_ROOT
WEIGHTS_PATH = '%s/weights.marshal' % GEN_ROOT

QUERY_SELECT = "SELECT vector, weight FROM tags WHERE name = ?"


def memo(func):
    """Memoize decorator."""
    cache = {}
    @wraps(func)
    def wrap(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrap


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


def get_vector(conn, tag, normalize=True):
    # TODO Legacy name. Clean up.
    return tag_features(tag, conn, normalize)


def tag_features(tag, conn=None, normalize=False):
    """Read a feature vector from the database.

    Small helper function that takes:
        conn - a connection to a SQLite database
        tag  - the name of a tag
    and returns the feature vector associated with the tag (or None if the tag
    wasn't found in the database).
    """
    if conn is None:
        conn = get_feature_db()
    res = conn.execute(QUERY_SELECT, (tag,)).fetchone()
    if res is None:
        return None, None
    raw, weight = res
    vector = list()
    for i in xrange(0, len(raw), 4):
        val, = struct.unpack('!f', raw[i:i+4])
        vector.append(val)
    if normalize:
        norm = math.sqrt(sum([x*x for x in vector]))
        if norm > 0:
            return tuple([x / norm for x in vector]), weight
    return tuple(vector), weight


def track_features(tags, conn=None, tag_fct=None):
    """Generate a feature vector for a track.

    The feature vector is entirely generated from the track's associated tags.
    Optionally, a function used to retrieve the tag features can be specified,
    which takes a single argument (the name of the tag). One use case is
    memoization:

        @utils.memo
        def tag_fct(tag):
            return utils.tag_features(tag, conn=conn)
    """
    if conn is None:
        conn = get_feature_db()
    if tag_fct is None:
        # Small closure around tag_features.
        tag_fct = lambda tag: tag_features(tag, conn=conn)
    vector = [0] * get_dimensions(conn)
    total = 0
    for tag, count in tags:
        if count == 0:
            continue
        curr, gw = tag_fct(tag)
        if curr is None:
            continue
        weight = gw * log1p(float(count)) / log(2)
        vector = [(weight*x + y) for x, y in zip(curr, vector)]
        total += weight
    # Normalizing the vector would make us lose independence of features.
    # However, we should still compensate for the document's length.
    return tuple([x / total for x in vector]) if total > 0 else None


def b64enc(raw):
    return base64.urlsafe_b64encode(raw).strip('=')


def b64dec(enc):
    padded = enc + '=' * (4 - len(enc) % 4)
    return base64.urlsafe_b64decode(padded)


def encode_features(features):
    raw = str()
    for val in features:
        raw += struct.pack('!f', val)
    return b64enc(raw).decode('ascii')


def decode_features(encoded):
    raw = b64dec(encoded)
    features = list()
    for i in xrange(0, len(raw), 4):
        val, = struct.unpack('!f', raw[i:i+4])
        features.append(val)
    return features


@memo
def get_dimensions(conn):
    res = conn.execute("SELECT vector FROM tags LIMIT 1").fetchone()
    return len(res[0]) / 4


def print_vector(vector, weight=None):
    # TODO Legacy name for print_features. Clean up.
    return print_features(vector, weight)


def print_features(vector, weight=None):
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


@memo
def get_config(path=None):
    """Get the configuration options for Unison."""
    if path is None:
        try:
            # Maybe an environment variable was set.
            path = '%s/config.yaml' % os.environ['UNISON_ROOT']
        except KeyError:
            # As a last resort, just try to find it in the working dir.
            path = 'config.yaml'
    return yaml.load(open(path))


def get_store(conn_str=None):
    """Get a Storm store for the Unison database."""
    if conn_str is None:
        conn_str = get_config()['database']['string']
    database = storm.locals.create_database(conn_str)
    return storm.locals.Store(database)


def get_feature_db(path=None):
    if path is None:
        path = get_config()['tagfeats']
    return sqlite3.connect(path)
