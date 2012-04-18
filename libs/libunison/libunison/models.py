#!/usr/bin/env python
from storm.locals import *

class User(Storm):
    __storm_table__ = 'user'
    uuid     = Unicode(primary=True)
    room_id  = Int()
    nickname = Unicode()
    model    = Unicode()
    # Relationships
    room         = Reference(room_id, 'Room.id')
    transactions = ReferenceSet(uuid, 'Transaction.master_id')
    lib_entries  = ReferenceSet(uuid, 'LibEntry.user_id')


class Room(Storm):
    __storm_table__ = 'room'
    id        = Int(primary=True)
    name      = Unicode()
    master_id = Unicode(name='master')
    # Relationships
    master       = Reference(master_id, 'User.uuid')
    users        = ReferenceSet(id, 'User.room_id')
    transactions = ReferenceSet(id, 'Transaction.room_id')


class Track(Storm):
    __storm_table__ = 'track'
    id       = Int(primary=True)
    artist   = Unicode()
    title    = Unicode()
    tags     = Unicode()
    features = Unicode()
    # Relationships
    transactions = ReferenceSet(id, 'Transaction.track_id')
    lib_entries  = ReferenceSet(id, 'LibEntry.track_id')


class LibEntry(Storm):
    __storm_table__ = 'libentry'
    id       = Int(primary=True)
    user_id  = Unicode()
    track_id = Int()
    local_id = Int()
    rating   = Int()
    # Relationships
    user  = Reference(user_id, 'User.uuid')
    track = Reference(track_id, 'Track.id')


class Transaction(Storm):
    __storm_table__ = 'transaction'
    id            = Int(primary=True)
    creation_time = DateTime()
    room_id       = Int()
    track_id      = Int()
    master_id     = Unicode(name='master')
    # Relationships
    room   = Reference(room_id, 'Room.id')
    track  = Reference(track_id, 'Track.id')
    master = Reference(master_id, 'User.uuid')


class Rating(Storm):
    __storm_table__ = 'rating'
    id            = Int(primary=True)
    user_id       = Unicode()
    creation_time = DateTime()
    artist        = Unicode()
    title         = Unicode()
    rating        = Int()
    # Relationships
    user = Reference(user_id, 'User.uuid')
