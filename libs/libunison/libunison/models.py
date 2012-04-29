#!/usr/bin/env python
from storm.locals import *
from _storm_ext import Point


class User(Storm):
    __storm_table__ = 'user'
    id = Int(primary=True)
    created = DateTime(name='creation_time')
    email = Unicode()
    is_email_valid = Bool(name='email_valid')
    password = Unicode()
    nickname = Unicode()
    room_id = Int()
    model = Unicode()
    # Relationships
    room = Reference(room_id, 'Room.id')
    lib_entries = ReferenceSet(id, 'LibEntry.user_id')

    def __init__(self, email=None, password=None):
        self.email = email
        self.password = password


class Room(Storm):
    __storm_table__ = 'room'
    id = Int(primary=True)
    created = DateTime(name='creation_time')
    name = Unicode()
    coordinates = Point()
    master_id = Int(name='master')
    is_active = Bool(name='active')
    # Relationships
    master = Reference(master_id, 'User.id')
    users = ReferenceSet(id, 'User.room_id')
    events = ReferenceSet(id, 'RoomEvent.room_id')

    def __init__(self, name=None, is_active=False):
        self.name = name
        self.is_active = is_active


class Track(Storm):
    __storm_table__ = 'track'
    id = Int(primary=True)
    artist = Unicode()
    title = Unicode()
    tags = Unicode()
    features = Unicode()
    # Relationships
    lib_entries = ReferenceSet(id, 'LibEntry.track_id')

    def __init__(self, artist, title):
        self.artist = artist
        self.title = title


class LibEntry(Storm):
    __storm_table__ = 'lib_entry'
    id = Int(primary=True)
    created = DateTime(name='creation_time')
    updated = DateTime(name='update_time')
    user_id = Int()
    track_id = Int()
    local_id = Int()
    is_valid = Bool(name='valid')
    is_local = Bool(name='local')
    rating = Int()
    # Relationships
    user = Reference(user_id, 'User.id')
    track = Reference(track_id, 'Track.id')

    def __init__(self, user=None, track=None, is_valid=False):
        self.user = user
        self.track = track
        self.is_valid = is_valid


class RoomEvent(Storm):
    __storm_table__ = 'room_event'
    id = Int(primary=True)
    created = DateTime(name='creation_time')
    room_id = Int()
    user_id = Int()
    event_type = Enum(map={
      # This is ridiculous. Whatever.
      u'play': u'play',
      u'rating': u'rating',
      u'join': u'join',
      u'leave': u'leave',
      u'skip': u'skip',
      u'master': u'master',
    })
    payload = JSON()
    # Relationships
    user = Reference(user_id, 'User.id')
    room = Reference(room_id, 'Room.id')

    def __init__(self, room, user, event_type, payload=None):
        self.room = room
        self.user = user
        self.event_type = event_type
        self.payload = payload
