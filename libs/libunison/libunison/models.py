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
    group_id = Int()
    model = Unicode()
    # Relationships
    group = Reference(group_id, 'Group.id')
    lib_entries = ReferenceSet(id, 'LibEntry.user_id')

    def __init__(self, email=None, password=None):
        self.email = email
        self.password = password


class Group(Storm):
    __storm_table__ = 'group'
    id = Int(primary=True)
    created = DateTime(name='creation_time')
    name = Unicode()
    coordinates = Point()
    master_id = Int(name='master')
    is_active = Bool(name='active')
    # Relationships
    master = Reference(master_id, 'User.id')
    users = ReferenceSet(id, 'User.group_id')
    events = ReferenceSet(id, 'GroupEvent.group_id')

    def __init__(self, name=None, is_active=False):
        self.name = name
        self.is_active = is_active


class Track(Storm):
    __storm_table__ = 'track'
    id = Int(primary=True)
    created = DateTime(name='creation_time')
    updated = DateTime(name='update_time')
    artist = Unicode()
    title = Unicode()
    image = Unicode()
    listeners = Int()
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


class GroupEvent(Storm):
    __storm_table__ = 'group_event'
    id = Int(primary=True)
    created = DateTime(name='creation_time')
    group_id = Int()
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
    group = Reference(group_id, 'Group.id')

    def __init__(self, group, user, event_type, payload=None):
        self.group = group
        self.user = user
        self.event_type = event_type
        self.payload = payload
