import sqlite3

from storm.locals import *


class User(Storm):
    __storm_table__ = 'user'
    id = Int(primary=True, name='ROWID')
    name = Unicode()
    tracks = ReferenceSet(id, 'UserTrack.uid', 'UserTrack.tid', 'Track.id')

    def __init__(self, name):
        self.name = name


class Track(Storm):
    __storm_table__ = 'track'
    id = Int(primary=True, name='ROWID')
    artist = Unicode()
    title = Unicode()
    tags = JSON()
    features = Unicode()
    users = ReferenceSet(id, 'UserTrack.tid', 'UserTrack.uid', 'User.id')

    def __init__(self, artist, title):
        self.artist = artist
        self.title = title


class UserTrack(Storm):
    __storm_table__ = 'user_track'
    id = Int(primary=True, name='ROWID')
    uid = Int()
    tid = Int()

    def __init__(self, user, track):
        self.uid = user.id
        self.tid = track.id


def init_db(store):
    store.execute("""
        CREATE TABLE IF NOT EXISTS user (name TEXT UNIQUE)""")
    store.execute("""
        CREATE TABLE IF NOT EXISTS track (
            artist TEXT,
            title TEXT,
            tags TEXT,
            features TEXT,
            UNIQUE (artist, title) ON CONFLICT IGNORE)""")
    store.execute("""
        CREATE TABLE IF NOT EXISTS user_track (
            uid INTEGER REFERENCES user,
            tid INTEGER REFERENCES track,
            UNIQUE (uid, tid) ON CONFLICT IGNORE)""")
