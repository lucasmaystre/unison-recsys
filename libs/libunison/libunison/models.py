#!/usr/bin/env python
from storm.locals import *
from _storm_ext import Point


class User(Storm):
    __storm_table__ = 'user'
    id = Int(primary=True)
    created = DateTime(name='creation_time')
    email = Unicode()
    password = Unicode()
    nickname = Unicode()
    room_id = Int()
    model = Unicode()
    # Relationships
    room = Reference(room_id, 'Room.id')
    lib_entries = ReferenceSet(id, 'LibEntry.user_id')


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


class Track(Storm):
    __storm_table__ = 'track'
    id = Int(primary=True)
    artist = Unicode()
    title = Unicode()
    tags = Unicode()
    features = Unicode()
    # Relationships
    lib_entries = ReferenceSet(id, 'LibEntry.track_id')


class LibEntry(Storm):
    __storm_table__ = 'lib_entry'
    id = Int(primary=True)
    created = DateTime(name='creation_time')
    updated = DateTime(name='update_time')
    user_id = Unicode()
    track_id = Int()
    local_id = Int()
    is_valid = Bool(name='valid')
    is_local = Bool(name='local')
    rating = Int()
    # Relationships
    user = Reference(user_id, 'User.id')
    track = Reference(track_id, 'Track.id')


class RoomEventType(Storm):
    __storm_table__ = 'room_event_type'
    id = Int(primary=True)
    name = Unicode()


class RoomEvent(Storm):
    __storm_table__ = 'room_event'
    id = Int(primary=True)
    created = DateTime(name='creation_time')
    room_id = Int()
    event_type_id = Int(name='event_type')
    payload = Unicode()
    # Relationships
    event_type = Reference(event_type_id, 'RoomEventType.id')
    room = Reference(room_id, 'Room.id')
