#!/usr/bin/env python

import argparse
import json
import liblfm
import mutagen
import os.path
import urllib
import urllib2

from libunison.utils import GEN_ROOT, get_config


CONFIG = get_config()
DEFAULT_FOLDER = '%s/metadata' % GEN_ROOT
API_ROOT = 'http://ws.audioscrobbler.com/2.0/'


def process(file_path):
    # Get the ID3 tags, fail if not present.
    meta = mutagen.File(file_path, easy=True)
    try:
        artist = meta.get('artist', []).pop(0)
    except IndexError:
        raise LookupError("file has no ID3 'artist' tag")
    try:
        title = meta.get('title', []).pop(0)
    except IndexError:
        raise LookupError("file has no ID3 'title' tag")
    if len(artist) == 0 or len(title) == 0:
        raise LookupError("'title' or 'artist' tag is empty")
    # Call the last.fm API to get the associated tags.
    lfm = liblfm.LastFM(CONFIG['lastfm']['key'])
    return {
      'artist': artist,
      'title': title,
      'tags': lfm.top_tags(artist, title),
    }


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='+')
    parser.add_argument('--dest', default=DEFAULT_FOLDER)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    folder = os.path.abspath(args.dest)
    if not os.path.exists(folder):
        os.makedirs(folder)
    for f in args.file:
        base = os.path.basename(f)
        try:
            print "Processing '%s'..." % f
            data = process(f)
        except LookupError as ve:
            print "Error with file: %s" % ve
            continue
        except urllib2.URLError as ue:
            print "Error with last.fm: %s" % ue.reason
            continue
        # Dump the metadata.
        meta = open('%s/%s.meta' % (folder, base), 'w')
        meta.write(json.dumps(data) + "\n")
        meta.close()
