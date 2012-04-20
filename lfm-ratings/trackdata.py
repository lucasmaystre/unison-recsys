#!/usr/bin/env python

import argparse
import json
import libunison.utils as uutils
import liblfm
import sqlite3
import sys
import urllib
import urllib2
import time


CONFIG = uutils.get_config()
DEFAULT_IN_DATABASE = 'gen/userdata.db'
DEFAULT_OUT_DATABASE = 'gen/trackdata.db'
API_ROOT = 'http://ws.audioscrobbler.com/2.0/'

DB_SCHEMA = """
    CREATE TABLE IF NOT EXISTS tracks(
      artist TEXT,
      title TEXT,
      tags TEXT,
      features TEXT
    );
    CREATE INDEX IF NOT EXISTS tracks_idx ON tracks(artist, title);
    """

QUERY_TRACK_EXISTS = 'SELECT 1 FROM tracks WHERE artist = ? AND title = ?'
QUERY_INSERT_TRACK = 'INSERT INTO tracks (artist, title, tags) VALUES (?, ?, ?)'

# 'in' database queries.
QUERY_GET_USER = 'SELECT ROWID FROM users WHERE name = ?'
QUERY_GET_TRACKS = 'SELECT artist, title FROM tracks WHERE user = ?'


def process(artist, title, db_conn):
    res = out_conn.execute(QUERY_TRACK_EXISTS, (artist, title)).fetchone()
    if res is not None:
        # Track is already in database.
        sys.stdout.write("-")
        sys.stdout.flush()
        return
    # Track not in database. We have to fetch the tags.
    time.sleep(1)
    lfm = liblfm.LastFM(CONFIG['lastfm']['key'])
    # Insert the metadata in the database.
    tags = json.dumps(lfm.top_tags(artist, title))
    db_conn.execute(QUERY_INSERT_TRACK, (artist, title, tags))
    db_conn.commit()
    sys.stdout.write(".")
    sys.stdout.flush()


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in-db', default=DEFAULT_IN_DATABASE)
    parser.add_argument('--out-db', default=DEFAULT_OUT_DATABASE)
    parser.add_argument('users')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    # Setup input DB
    in_conn = sqlite3.connect(args.in_db)
    # Setup output DB.
    out_conn = sqlite3.connect(args.out_db)
    out_conn.executescript(DB_SCHEMA)
    for line in open(args.users):
        user = line.strip()
        print "processing user '%s'" % user
        res = in_conn.execute(QUERY_GET_USER, (user,)).fetchone()
        if res is None:
            print "user not found."
            continue
        uid = res[0]
        for row in in_conn.execute(QUERY_GET_TRACKS, (uid,)).fetchall():
            try:
                process(row[0], row[1], out_conn)
            except Exception as e:
                print "problem while processing (%s, %s): %s" % (
                        row[0], row[1], e)
        print ''
