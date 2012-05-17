#!/usr/bin/env python
"""Wrapper around the Last.fm web API."""

import json
import urllib
import urllib2


class LastFM(object):
    API_ROOT = 'http://ws.audioscrobbler.com/2.0/'
    IMAGE_SIZE = {
      'DEFAULT': 0,
      'small': 1,
      'medium': 2,
      'large': 3,
      'extralarge': 4,
    }

    def __init__(self, key):
        self._key = key

    def track_info(self, artist, title):
        """Get various track metadata.

        Currently, it returns a dict with the following information:
        - 'listeners': number of people listening to this song on last.fm
        - 'image': a URL to an image representing the track (usually a cover)
        """
        # Implementation detail: the 'artist' parameter seems to be broken on
        # the last.fm API (e.g. with Deadmau5 - Strobe). It seems to work better
        # to put both artist and title in the query parameter named 'track', and
        # hope for the best.
        params = {
          'format' : 'json',
          'api_key': self._key,
          'method' : 'track.search',
          'limit'  : '1',  # Just return the first result.
          'track'  : "%s %s" % (title.encode('utf-8'), artist.encode('utf-8')),
        }
        query_str = urllib.urlencode(params)
        res = urllib2.urlopen(self.API_ROOT, query_str).read()
        data = json.loads(res)
        if type(data) is not dict:
            raise LookupError('last.fm returned garbage')
        if 'results' not in data or type(data['results']) is not dict:
            raise LookupError('last.fm returned: %r' % res)
        matches = data['results'].get('trackmatches')
        if type(matches) is not dict:
            raise LookupError('track not found')
        track = matches.get('track')
        if type(track) is not dict:
            raise LookupError('track is not a dict? WTF?')
        img_url = None
        if 'image' in track:
            current_size = -1
            for item in track['image']:
                size = item.get('size', 'DEFAULT')
                if '#text' in item and self.IMAGE_SIZE[size] > current_size:
                    img_url = item['#text']
                    current_size = self.IMAGE_SIZE[size]
        return {
          'title': track.get('name'),
          'artist': track.get('artist'),
          'image': img_url,
          'listeners': int(track.get('listeners', 0)),
        }

    def top_tags(self, artist, title):
        """Get the top tags for a track."""
        params = {
          'format'     : 'json',
          'api_key'    : self._key,
          'method'     : 'track.gettoptags',
          'autocorrect': '1',
          'artist'     : artist.encode('utf-8'),
          'track'      : title.encode('utf-8'),
        }
        query_str = urllib.urlencode(params)
        res = urllib2.urlopen(self.API_ROOT, query_str).read()
        data = json.loads(res)
        if type(data) is not dict:
            raise LookupError('last.fm returned garbage.')
        if 'toptags' not in data:
            if int(data.get('error', 0)) == 6:
                raise LookupError("Track not found")
            else:
                raise LookupError("last.fm returned: %r" % res)
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
            raise LookupError('last.fm returned: %r' % data)
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
