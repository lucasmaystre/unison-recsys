#!/usr/bin/env python
"""Constants used by the API."""


class Namespace(object):
    """Dummy class used to namespace constants."""
    pass


# API errors.
errors = Namespace()
errors.MISSING_FIELD = 0x01
errors.EXISTING_USER = 0x02
errors.INVALID_RATING = 0x03
errors.INVALID_EMAIL = 0x04
errors.INVALID_PASSWORD = 0x05
errors.INVALID_ROOM = 0x06
errors.INVALID_TRACK = 0x07
errors.INVALID_LIBENTRY = 0x08
errors.INVALID_DELTA = 0x09
errors.UNAUTHORIZED = 0x0a
errors.TRACKS_DEPLETED = 0x0b
errors.MASTER_TAKEN = 0x0c

# Room events.
events = Namespace()
events.RATING = u'rating'
events.JOIN = u'join'
events.LEAVE = u'leave'
events.PLAY = u'play'
events.SKIP = u'skip'
events.MASTER = u'master'
