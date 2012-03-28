#!/usr/bin/env python

import argparse
import json
import mutagen
import os.path
import urllib
import urllib2

from util import GEN_ROOT


DEFAULT_KEY_FILE = 'lastfm.key'
DEFAULT_FOLDER = '%s/metadata' % GEN_ROOT
API_ROOT = 'http://ws.audioscrobbler.com/2.0/'


def process(file_path, api_key):
    # Get the ID3 tags, fail if not present.
    meta = mutagen.File(file_path, easy=True)
    try:
        artist = meta.get('artist', []).pop(0)
    except IndexError:
        raise ValueError("file has no ID3 'artist' tag")
    try:
        title = meta.get('title', []).pop(0)
    except IndexError:
        raise ValueError("file has no ID3 'title' tag")
    if len(artist) == 0 or len(title) == 0:
        raise ValueError("'title' or 'artist' tag is empty")
    # Call the last.fm API to get the associated tags.
    res = lastfm_toptags(artist, title, api_key)
    if 'toptags' not in res:
        raise ValueError("last.fm says '%s'" % res.get('message'))
    toptags = res['toptags'].get('tag', [])
    # When there is a single tag, last.fm doesn't wrap it in an array.
    if type(toptags) is dict:
        toptags = [toptags]
    # Return a dict with the metadata in the last.fm MSD format.
    tags = [[tag['name'], tag['count']] for tag in toptags]
    return {
      'artist': artist,
      'title': title,
      'tags': tags,
    }


def lastfm_toptags(artist, title, api_key):
    params = {
      'format'     : 'json',
      'api_key'    : api_key,
      'method'     : 'track.gettoptags',
      'autocorrect': '1',
      'artist'     : artist.encode('utf-8'),
      'track'      : title.encode('utf-8')
    }
    query_str = urllib.urlencode(params)
    res = urllib2.urlopen(API_ROOT, query_str).read()
    return json.loads(res)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='+')
    parser.add_argument('--key', default=DEFAULT_KEY_FILE)
    parser.add_argument('--dest', default=DEFAULT_FOLDER)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    api_key = open(args.key).read().strip()
    folder = os.path.abspath(args.dest)
    if not os.path.exists(folder):
        os.makedirs(folder)
    for f in args.file:
        base = os.path.basename(f)
        try:
            print "Processing '%s'..." % f
            data = process(f, api_key)
        except ValueError as ve:
            print "Error with file: %s" % ve
            continue
        except urllib2.URLError as ue:
            print "Error with last.fm: %s" % ue.reason
            continue
        # Dump the metadata.
        meta = open('%s/%s.meta' % (folder, base), 'w')
        meta.write(json.dumps(data) + "\n")
        meta.close()
