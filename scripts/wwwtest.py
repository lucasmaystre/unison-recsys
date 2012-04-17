#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import requests


DEFAULT_UUID = "00000000-0000-0000-0000-0000deadbeef"


class UnisonGetter:

    URL_FORMAT = "http://unison.local/api%s"
    
    def __init__(self, uuid):
        self.headers = {'Unison-UUID': uuid}
    
    def __getattr__(self, name):
        getter = getattr(requests, name)
        def wrapper(path, data=None):
            url = self.URL_FORMAT % path
            res = getter(url, data=data, headers=self.headers)
            print "URL:    %s" % url
            print "method: %s" % name.upper()
            print "data:   %s" % str(data)
            print "status: %s" % res.status_code
            print "----------------------------------------"
            print res.text
            print "========================================"
        return wrapper


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--uuid', default=DEFAULT_UUID)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    unison = UnisonGetter(args.uuid)

    unison.get('/')
    # Create or update user (should never fail).
    raw_input()
    unison.put('/users/%s' % args.uuid, {'nickname': u'ashléàôbad'})
    # Join room that exists.
    raw_input()
    unison.put('/users/%s/room' % args.uuid, {'room': 1})
    # Join room that DOESN'T exist.
    raw_input()
    unison.put('/users/%s/room' % args.uuid, {'room': 9999999})
    # Leave room.
    raw_input()
    unison.delete('/users/%s/room' % args.uuid)
    # Try to make someone else leave the room :-)
    raw_input()
    unison.delete('/users/%s/room' % 'hello-hows-it-going')
    # Get infos about ALL the rooms.
    raw_input()
    unison.get('/rooms')
    # Create a new room.
    raw_input()
    unison.post('/rooms', {'name': u'test-rööm'})
    # Get infos about room
    raw_input()
    unison.get('/rooms/%d' % 1)
    # Get infos about room - badly formatted.
    raw_input()
    unison.get('/rooms/%s' % 'blabla')
    # Get the next track for the room.
    raw_input()
    unison.post('/rooms/%d' % 1)
    # Join another room.
    raw_input()
    unison.put('/users/%s/room' % args.uuid, {'room': 2})
    # Take the master position for a room that doesn't have one.
    raw_input()
    unison.put('/rooms/%d/master' % 2, {'user': args.uuid})
    # Take the master position for a room that we're not in.
    raw_input()
    unison.put('/rooms/%d/master' % 1, {'user': args.uuid})
    # Leave DJ position.
    raw_input()
    unison.delete('/rooms/%d/master' % 2, {'user': args.uuid})
    # Leave DJ position as second time. Should fail (not idempotent...)
    raw_input()
    unison.delete('/rooms/%d/master' % 2, {'user': args.uuid})
