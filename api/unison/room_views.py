#!/usr/bin/env python
"""Room-related views."""

import helpers
import random

from constants import errors, events
from flask import Blueprint, request, g, jsonify
from libentry_views import set_rating
from libunison.models import User, Room, Track, LibEntry, RoomEvent
from storm.expr import Desc


room_views = Blueprint('room_views', __name__)


@room_views.route('', methods=['GET'])
@helpers.authenticate()
def list_rooms():
    """Get a list of rooms."""
    # TODO Search rooms that are nearby
    # See http://archives.postgresql.org/pgsql-novice/2005-02/msg00196.php
    rooms = list()
    for room in g.store.find(Room, Room.is_active):
        rooms.append({
          'rid': room.id,
          'name': room.name,
          'nb_users': room.users.count()
        })
    return jsonify(rooms=rooms)


@room_views.route('', methods=['POST'])
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
    play_event = results.order_by(Desc(RoomEvent.created)).first()
    track = None
    if play_event is not None:
        track = {
          'artist': play_event.payload.get('artist'),
          'title': play_event.payload.get('title'),
        }
        for entry in play_event.payload.get('stats', []):
            if entry.get('uid') in userdict:
                uid = entry['uid']
                userdict[uid]['score'] = entry.get('score')
                userdict[uid]['predicted'] = entry.get('predicted', True)
    users = list()
    for key, val in userdict.iteritems():
        users.append({
          'uid': key,
          'nickname': val.get('nickname'),
          'score': val.get('score'),
          'predicted': val.get('predicted', True)
        })
    master = None
    if room.master is not None:
        master = {
          'uid': room.master.id,
          'nickname': room.master.nickname
        }
    return jsonify(name=room.name, track=track, master=master, users=users)


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
    entries = list(g.store.find(LibEntry, (LibEntry.user == user)
            & (LibEntry.is_valid == True) & (LibEntry.is_local == True)))
    if len(entries) == 0:
        raise helpers.NotFound(errors.TRACKS_DEPLETED,
                'no more tracks to play')
    entry = random.choice(entries)
    return jsonify({
      'artist': entry.track.artist,
      'title': entry.track.title,
      'local_id': entry.local_id,
    })


@room_views.route('/<int:rid>/current', methods=['PUT'])
@helpers.authenticate(with_user=True)
def play_track(user, rid):
    """Register the track that is currently playing."""
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
      'master': {'uid': user.id, 'nickname': user.nickname},
    }
    payload['stats'] = list()
    # TODO Something better than random scores :)
    for resident in room.users:
        payload['stats'].append({
          'uid': resident.id,
          'nickname': resident.nickname,
          'score': int(random.random() * 100),
          'predicted': True if random.random() > 0.2 else False
        })
    event = RoomEvent(room, user, events.PLAY, payload)
    g.store.add(event)
    return helpers.success()


@room_views.route('/<int:rid>/current', methods=['DELETE'])
@helpers.authenticate(with_user=True)
def skip_track(user, rid):
    """Skip the track that is currently being played."""
    room = g.store.get(Room, rid)
    if room is None:
        raise helpers.BadRequest(errors.INVALID_ROOM,
                "room does not exist")
    if room.master != user:
        raise helpers.Unauthorized("you are not the master")
    results = g.store.find(RoomEvent,
            (RoomEvent.event_type == events.PLAY) & (RoomEvent.room == room))
    play_event = results.order_by(Desc(RoomEvent.created)).first()
    if play_event is None:
        raise helpers.BadRequest(errors.NO_CURRENT_TRACK,
                "no track to skip")
    payload = {
      'artist': play_event.payload.get('artist'),
      'title': play_event.payload.get('title'),
      'master': {'uid': user.id, 'nickname': user.nickname},
    }
    event = RoomEvent(room, user, events.SKIP, payload)
    g.store.add(event)
    return helpers.success()


@room_views.route('/<int:rid>/ratings', methods=['POST'])
@helpers.authenticate(with_user=True)
def add_rating(user, rid):
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
        uid = int(request.form['uid'])
    except KeyError, ValueError:
        raise helpers.BadRequest(errors.MISSING_FIELD,
                "cannot parse uid")
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
