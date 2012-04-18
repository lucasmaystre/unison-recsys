#!/usr/bin/env python
"""Wrapper around the Last.fm web API."""

import json
import urllib
import urllib2


class LastFM(object):
    API_ROOT = 'http://ws.audioscrobbler.com/2.0/'

    def __init__(self, key):
        self._key = key

    def top_tags(self, artist, title):
        """Get the top tags for a track."""
        params = {
          'format'     : 'json',
          'api_key'    : self._key,
          'method'     : 'track.gettoptags',
          'autocorrect': '1',
          'artist'     : artist.encode('utf-8'),
          'track'      : title.encode('utf-8')
        }
        query_str = urllib.urlencode(params)
        res = urllib2.urlopen(self.API_ROOT, query_str).read()
        data = json.loads(res)
        if type(data) is not dict:
            raise LookupError('last.fm returned garbage.')
        if 'toptags' not in data:
            raise ValueError("last.fm says '%s'" % res.get('message'))
        toptags = data['toptags'].get('tag', [])
        # When there is a single tag, last.fm doesn't wrap it in an array.
        if type(toptags) is dict:
            toptags = [toptags]
        return tuple((tag['name'], int(tag['count'])) for tag in toptags)

    def banned_tracks(self, user, page=1, limit=50):
        """Get a user's banned tracks."""
        return self._get_tracks('bannedtracks', user, page, limit)

    def loved_tracks(self, user, page=1, limit=50):
        """Get a user's loved tracks."""
        return self._get_tracks('lovedtracks', user, page, limit)

    def _get_tracks(self, what, user, page, limit):
        params = {
          'format' : 'json',
          'api_key': self._key,
          'method' : 'user.get%s' % what,
          'user'   : user.encode('utf-8'),
          'page'   : page,
          'limit'  : limit,
        }
        query_str = urllib.urlencode(params)
        res = urllib2.urlopen(self.API_ROOT, query_str).read()
        data = json.loads(res)
        if type(data) is not dict:
            raise LookupError('last.fm returned garbage.')
        root = data.get(what)
        if root is None:
            raise LookupError('last.fm says: %r' % data)
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
