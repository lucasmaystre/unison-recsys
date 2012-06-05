#!/usr/bin/env python

import argparse
import libunison.utils as uutils
import sys

from db import *
from lxml import etree
from storm.locals import *


DEFAULT_DB = 'gen/itunes.db'
CONFIG = uutils.get_config()


def get_tracks(path):
    tracks = list()
    error_count = 0
    doc = etree.parse(open(path))
    for track in doc.xpath("/plist/dict/key[. = 'Tracks']"
            "/following-sibling::dict[1]/dict"):
        try:
            artist = track.xpath("key[. ='Artist']"
                    "/following-sibling::string[1]")[0]
            title = track.xpath("key[. ='Name']"
                    "/following-sibling::string[1]")[0]
        except IndexError:
            error_count += 1
            continue
        tracks.append({
          'artist': unicode(artist.text),
          'title': unicode(title.text),
        })
    return tracks, error_count


def save_tracks(store, username, tracks):
    user = store.find(User, User.name == username).one()
    if user is None:
        user = User(username)
        store.add(user)
    for meta in tracks:
        track = store.find(Track, (Track.artist == meta['artist'])
                & (Track.title == meta['title'])).one()
        if track is None:
            track = Track(meta['artist'], meta['title'])
            store.add(track)
        store.flush()
        link = UserTrack(user, track)
        store.add(link)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('user', type=unicode)
    parser.add_argument('file')
    parser.add_argument('--db', default=DEFAULT_DB)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    # Parse the tracks from the XML.
    tracks, error_count = get_tracks(args.file)
    print "Nb parsed tracks:  %d" % len(tracks)
    print "Nb parsing errors: %d" % error_count
    # Save tracks into the database.
    store = Store(create_database('sqlite:%s' % args.db))
    init_db(store)
    save_tracks(store, args.user, tracks)
    store.commit()
    store.close()
