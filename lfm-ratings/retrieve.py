#!/usr/bin/env python

import argparse
import httplib
import json
import liblfm
import libunison.utils as uutils
import sqlite3
import sys
import time
import urllib
import urllib2


CONFIG = uutils.get_config()
DEFAULT_DATABASE = 'gen/userdata.db'
DEFAULT_MAX_PAGES = 10

DB_SCHEMA = """
    CREATE TABLE IF NOT EXISTS users(name TEXT);
    CREATE TABLE IF NOT EXISTS tracks(
      user INTEGER,
      status TEXT,
      artist TEXT,
      title TEXT,
      timestamp INTEGER
    );
    """
SELECT_USER = 'SELECT ROWID FROM users WHERE name = ?'
INSERT_USER = 'INSERT INTO users (name) VALUES (?)'
INSERT_TRACK = ('INSERT INTO tracks (user, status, artist, title, timestamp) '
        + 'VALUES (?, ?, ?, ?, ?)')


def process(user, max_pages, conn):
    lfm = liblfm.LastFM(CONFIG['lastfm']['key'])
    id = select_or_insert(user, conn)
    # Get the banned tracks.
    subset, pages = lfm.banned_tracks(user)
    banned = list(subset)
    for i in xrange(2, min(pages, max_pages) + 1):
        subset, pages = lfm.banned_tracks(user, page=i)
        banned.extend(subset)
    insert_tracks('banned', banned, id, conn)
    print " (banned: done)"
    # Get the loved tracks.
    subset, pages = lfm.loved_tracks(user)
    loved = list(subset)
    for i in xrange(2, min(pages, max_pages) + 1):
        subset, pages = lfm.loved_tracks(user, page=i)
        loved.extend(subset)
    insert_tracks('loved', loved, id, conn)
    print " (loved: done)"


def insert_tracks(status, tracks, user, conn):
    for track in tracks:
        conn.execute(INSERT_TRACK, (user, status, 
                track['artist'], track['title'], track['timestamp']))
    conn.commit()


def select_or_insert(user, conn):
    c = conn.cursor()
    res = c.execute(SELECT_USER, (user,)).fetchone()
    if res is not None:
        return res[0]
    # User doesn't exist, we have to create it.
    c.execute(INSERT_USER, (user,))
    id = c.lastrowid
    conn.commit()
    return id


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=DEFAULT_DATABASE)
    parser.add_argument('--max-pages', type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument('users')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    conn = sqlite3.connect(args.db)
    conn.executescript(DB_SCHEMA)
    for line in open(args.users):
        user = line.strip()
        print "Processing user '%s'..." % user
        try:
            process(user, args.max_pages, conn)
        except (urllib2.URLError, ValueError, LookupError) as error:
            print "Error: %s" % error
        except (httplib.HTTPException) as error:
            # This happens sometimes, when the HTTP status code is unknown.
            print "Error: %s" % error
