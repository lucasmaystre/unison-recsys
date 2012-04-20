#!/usr/bin/env python

import argparse
import httplib
import json
import libunison.utils as uutils
import sqlite3
import sys
import time
import urllib
import urllib2


CONFIG = uutils.get_config()
DEFAULT_DATABASE = 'gen/userdata.db'
DEFAULT_MAX_PAGES = 10
API_ROOT = 'http://ws.audioscrobbler.com/2.0/'

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


def get_tracks(what, user, page, limit):
    time.sleep(1)
    params = {
      'format' : 'json',
      'api_key': CONFIG['lastfm']['key'],
      'method' : 'user.get%s' % what,
      'user'   : user.encode('utf-8'),
      'page'   : page,
      'limit'  : limit,
    }
    query_str = urllib.urlencode(params)
    response = urllib2.urlopen(API_ROOT, query_str).read()
    sys.stdout.write('.')
    sys.stdout.flush()
    data = json.loads(response)
    if type(data) is not dict:
        raise LookupError('last.fm returned garbage.')
    root = data.get(what)
    if root is None:
        raise LookupError('last.fm says: %s' % data.get('message'))
    attrs = root.get('@attr')
    if attrs is None:
        # There are no tracks (XML attributes have been inlined in the JSON).
        return ([], 0)
    pages = attrs.get('totalPages', 0)
    tracks = root.get('track')
    if tracks is None:
        raise LookupError('could not find tracks in JSON file')
    # When there is a single track, last.fm doesn't wrap it in an array.
    if type(tracks) is dict:
        tracks = [tracks]
    elems = list()
    for track in tracks:
        elems.append({
          'artist'   : track.get('artist', {}).get('name', '').strip(),
          'title'    : track.get('name', '').strip(),
          'timestamp': int(track.get('date', {}).get('uts', 0)),
        })
    return (elems, int(pages))


def get_banned(user, page=1, limit=50):
    return get_tracks('bannedtracks', user, page, limit)


def get_loved(user, page=1, limit=50):
    return get_tracks('lovedtracks', user, page, limit)


def process(user, max_pages, conn):
    id = select_or_insert(user, conn)
    # Get the banned tracks.
    #subset, pages = get_banned(user)
    #banned = list(subset)
    #for i in xrange(2, min(pages, max_pages) + 1):
    #    subset, pages = get_banned(user, page=i)
    #    banned.extend(subset)
    #insert_tracks('banned', banned, id, conn)
    #print " (banned: done)"
    # Get the loved tracks.
    subset, pages = get_loved(user)
    loved = list(subset)
    for i in xrange(2, min(pages, max_pages) + 1):
        subset, pages = get_loved(user, page=i)
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
