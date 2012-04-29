#!/usr/bin/env python
"""Room-related views."""

import helpers

from constants import errors, events
from flask import Blueprint, request, g, jsonify
from libentry_views import set_rating
from libunison.models import User, Room, Track, LibEntry, RoomEvent
from storm.expr import Desc


room_views = Blueprint('room_views', __name__)


@room_views.route('/', methods=['GET'])
@helpers.authenticate()
def list_rooms():
    """Get a list of rooms."""
    # TODO Search rooms that are nearby
    # See http://archives.postgresql.org/pgsql-novice/2005-02/msg00196.php
    rooms = list()
    for room in g.store.find(Room, Room.is_active):
        rooms.append({
          'id': room.id,
          'name': room.name,
          'participants': room.users.count()
        })
    return jsonify(rooms=rooms)


@room_views.route('/', methods=['POST'])
@helpers.authenticate()
def create_room():
    """Create a new room."""
    try:
        name = request.form['name']
    except KeyError:
        raise helpers.BadRequest(errors.MISSING_FIELD,
                "room name is missing")
    room = Room(name, is_active=True)
    room.coordinates = (0, 0)  # TODO store the real coordinates.
    g.store.add(room)
    return list_rooms()


@room_views.route('/<int:rid>', methods=['GET'])
@helpers.authenticate()
def get_room_info(rid):
    """Get infos about the specified room.

    Includes:
    - participants in the room (ID, nickname & stats)
    - current DJ (ID & nickname)
    - info about last track
    """
    room = g.store.get(Room, rid)
    if room is None:
        raise helpers.BadRequest(errors.INVALID_ROOM,
                "room does not exist")
    userdict = dict()
    for user in room.users:
        userdict[user.id] = {'nickname': user.nickname}
    # Search for the last track that was played.
    results = g.store.find(RoomEvent,
            (RoomEvent.event_type == events.PLAY) & (RoomEvent.room == room))
    for row in results:
        print row
    play_event = results.order_by(Desc(RoomEvent.created)).first()
    track = None
    if play_event is not None:
        track = {
          'artist': play_event.payload.get('artist'),
          'title': play_event.payload.get('title'),
        }
        for entry in play_event.payload.get('stats', []):
            if entry.get('id') in userdict:
                userdict[entry['id']]['score'] = entry.get('score')
                userdict[entry['id']]['predicted'] = entry.get('predicted', True)
    users = list()
    for key, val in userdict.iteritems():
        users.append({
          'id': key,
          'nickname': val.get('nickname'),
          'score': val.get('score'),
          'predicted': val.get('predicted', True)
        })
    master = None
    if room.master is not None:
        master = {
          'id': room.master.id,
          'nickname': room.master.nickname
        }
    return jsonify(track=track, master=master, users=users)


@room_views.route('/<int:rid>', methods=['POST'])
@helpers.authenticate(with_user=True)
def get_track(user, rid):
    """Get the next track."""
    room = g.store.get(Room, rid)
    if room is None:
        raise helpers.BadRequest(errors.INVALID_ROOM,
                "room does not exist")
    if room.master != user:
        raise helpers.Unauthorized("you are not the DJ")
    # TODO Something better than a random song :)
    entry = g.store.find(LibEntry, (LibEntry.user == user)
            & (LibEntry.is_valid == True) & (LibEntry.is_local == True)).any()
    if entry is None:
        raise helpers.NotFound(errors.TRACKS_DEPLETED,
                'no more tracks to play')
    return jsonify({
      'artist': entry.track.artist,
      'title': entry.track.title,
      'local_id': entry.local_id,
    })


@room_views.route('/<int:rid>/current', methods=['PUT', 'DELETE'])
@helpers.authenticate(with_user=True)
def play_skip_track(user, rid):
    room = g.store.get(Room, rid)
    if room is None:
        raise helpers.BadRequest(errors.INVALID_ROOM,
                "room does not exist")
    if room.master != user:
        raise helpers.Unauthorized("you are not the master")
    try:
        artist = request.form['artist']
        title = request.form['title']
    except KeyError:
        raise helpers.BadRequest(errors.MISSING_FIELD,
                "missing artist and / or title")
    track = g.store.find(Track,
            (Track.artist == artist) & (Track.title == title)).one()
    if track is None:
        raise helpers.BadRequest(errors.INVALID_TRACK,
                "track not found")
    payload = {
      'artist': track.artist,
      'title': track.title,
      'master': {'id': user.id, 'nickname': user.nickname},
    }
    if request.method == 'PUT':
        # We're playing a new song.
        payload['users'] = list()
        # TODO Something better than random scores :)
        for resident in room.users:
            payload['users'].append({
              'id': resident.id,
              'nickname': resident.nickname,
              'score': int(random.random() * 100),
              'predicted': True if random.random() > 0.2 else False
            })
    else:  # request.method == 'DELETE'
        # We're skipping the song.
        event_type = events.SKIP
    event = RoomEvent(room, user, event_type, payload)
    g.store.add(event)
    return helpers.success()


@room_views.route('/<int:rid>/ratings', methods=['POST'])
@helpers.authenticate(with_user=True)
def set_master(user, rid):
    """Take the DJ spot (if it is available)."""
    room = g.store.get(Room, rid)
    if room is None:
        raise helpers.BadRequest(errors.INVALID_ROOM,
                "room does not exist")
    try:
        artist = request.form['artist']
        title = request.form['title']
        rating = max(1, min(5, int(request.form['rating'])))
    except KeyError:
        raise helpers.BadRequest(errors.MISSING_FIELD,
                "missing artist, title or rating")
    except ValueError:
        raise helpers.BadRequest(errors.INVALID_RATING,
                "rating is invalid")
    if user.room != room:
        raise helpers.Unauthorized("you are not in this room")
    track = g.store.find(Track,
            (Track.artist == artist) & (Track.title == title)).one()
    if track is None:
        raise helpers.BadRequest(errors.INVALID_TRACK,
                "track not found")
    # Add a room event.
    event = RoomEvent(room, user, events.RATING)
    event.payload = {
     'artist': track.artist,
     'title': track.artist,
     'rating': rating,
    }
    g.store.add(event)
    # Add a library entry.
    set_rating(user, track.artist, track.title, rating)
    return helpers.success()


@room_views.route('/<int:rid>/master', methods=['PUT'])
@helpers.authenticate(with_user=True)
def set_master(user, rid):
    """Take the DJ spot (if it is available)."""
    room = g.store.get(Room, rid)
    if room is None:
        raise helpers.BadRequest(errors.INVALID_ROOM,
                "room does not exist")
    try:
        uid = request.form['user']
    except KeyError:
        raise helpers.BadRequest(errors.MISSING_FIELD,
                "missing user")
    if user.id != uid or user.room != room:
        raise helpers.Unauthorized("user not self or not in room")
    if room.master != None:
        raise helpers.Unauthorized("someone else is already here")
    room.master = user
    return helpers.success()


@room_views.route('/<int:rid>/master', methods=['DELETE'])
@helpers.authenticate(with_user=True)
def leave_master(user, rid):
    """Leave the DJ spot."""
    room = g.store.get(Room, rid)
    if room is None:
        raise helpers.BadRequest(errors.INVALID_ROOM,
                "room does not exist")
    if room.master != user:
        raise helpers.Unauthorized("you are not the master")
    room.master = None
    return helpers.success()
