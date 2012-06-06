#!/usr/bin/env python
"""Room-related views."""

import datetime
import helpers
import libunison.geometry as geometry
import libunison.predict as predict
import random
import time

from constants import errors, events
from flask import Blueprint, request, g, jsonify
from libentry_views import set_rating
from libunison.models import User, Room, Track, LibEntry, RoomEvent
from operator import itemgetter
from storm.expr import Desc


# Maximal number of rooms returned when listing rooms.
MAX_ROOMS = 10

# Maximal number of tracks returned when asking for the next tracks.
MAX_TRACKS = 5

# Interval during which we don't play the same song again.
ACTIVITY_INTERVAL = 60 * 60 * 5  # In seconds.

room_views = Blueprint('room_views', __name__)


@room_views.route('', methods=['GET'])
@helpers.authenticate()
def list_rooms():
    """Get a list of rooms."""
    userloc = None
    try:
        lat = float(request.values['lat'])
        lon = float(request.values['lon'])
    except (KeyError, ValueError):
        # Sort by descending ID - new rooms come first.
        key_fct = lambda r: -1 * r.id
    else:
        # Sort the rows according to the distance from the user's location.
        userloc = geometry.Point(lat, lon)
        key_fct = lambda r: geometry.distance(userloc, r.coordinates)
    rooms = list()
    rows = sorted(g.store.find(Room, Room.is_active), key=key_fct)
    for room in rows[:MAX_ROOMS]:
        rooms.append({
          'rid': room.id,
          'name': room.name,
          'nb_users': room.users.count(),
          'distance': (geometry.distance(userloc, room.coordinates)
                  if userloc is not None else None),
        })
    return jsonify(rooms=rooms)


@room_views.route('', methods=['POST'])
@helpers.authenticate()
def create_room():
    """Create a new room."""
    try:
        name = request.form['name']
        lat = float(request.form['lat'])
        lon = float(request.form['lon'])
    except (KeyError, ValueError):
        raise helpers.BadRequest(errors.MISSING_FIELD,
                "room name, latitude or longitude is missing or invalid")
    room = Room(name, is_active=True)
    room.coordinates = geometry.Point(lat, lon)
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
    track = None
    play_event = results.order_by(Desc(RoomEvent.created)).first()
    if play_event is not None:
        artist = play_event.payload.get('artist')
        title = play_event.payload.get('title')
        row = g.store.find(Track, (Track.artist == artist)
                & (Track.title == title)).one()
        image = row.image if row is not None else None
        track = {
          'artist': artist,
          'title': title,
          'image': image,
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


def get_played_filter(room):
    played = set()
    threshold = datetime.datetime.fromtimestamp(
            time.time() - ACTIVITY_INTERVAL)
    events = g.store.find(RoomEvent, (RoomEvent.room == room)
        & (RoomEvent.event_type == u'play') & (RoomEvent.created > threshold))
    for event in events:
        info = (event.payload.get(artist), event.payload.get(title))
        played.add(info)
    def played_filter(entry):
        info = (entry.track.artist, entry.track.title)
        return info not in played
    return played_filter


@room_views.route('/<int:rid>', methods=['POST'])
@helpers.authenticate(with_user=True)
def get_track(master, rid):
    """Get the next track."""
    room = g.store.get(Room, rid)
    if room is None:
        raise helpers.BadRequest(errors.INVALID_ROOM,
                "room does not exist")
    if room.master != master:
        raise helpers.Unauthorized("you are not the DJ")
    # Get all the tracks in the master's library that haven't been played.
    played_filter = get_played_filter(room)
    remaining = filter(played_filter, g.store.find(LibEntry,
            (LibEntry.user == master) & (LibEntry.is_valid == True)
            & (LibEntry.is_local == True)))
    if len(remaining) == 0:
        raise helpers.NotFound(errors.TRACKS_DEPLETED,
                'no more tracks to play')
    # Partition tracks based on whether we can embed them in the latent space.
    with_feats = list()
    points = list()
    no_feats = list()
    for entry in remaining:
        point = predict.get_point(entry.track)
        if point is not None:
            with_feats.append(entry)
            points.append(point)
        else:
            no_feats.append(entry)
    print repr(with_feats)
    print repr(no_feats)
    # For the users that can be modelled: predict their ratings.
    models = filter(lambda model: model.is_nontrivial(),
            [predict.Model(user) for user in room.users])
    print repr(models)
    if models is not None:
        ratings = [model.score(points) for model in models]
        print repr(ratings)
        agg = predict.aggregate(ratings)
        print repr(agg)
    else:
        # Not a single user can be modelled! just order the songs randomly.
        agg = range(len(with_feats))
        random.shuffle(agg)
    # Construct the playlist, decreasing order of scores.
    playlist = [entry for entry, score in sorted(
            zip(with_feats, agg), key=itemgetter(1), reverse=True)]
    # Randomize songs for which we don't have features.
    random.shuffle(no_feats)
    playlist.extend(no_feats)
    # Craft the JSON response.
    tracks = list()
    for entry in playlist[:MAX_TRACKS]:
        tracks.append({
          'artist': entry.track.artist,
          'title': entry.track.title,
          'local_id': entry.local_id,
        })
    return jsonify(tracks=tracks)


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
     'title': track.title,
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
    except (KeyError, ValueError):
        raise helpers.BadRequest(errors.MISSING_FIELD,
                "cannot parse uid")
    if user.id != uid or user.room != room:
        raise helpers.Unauthorized("user not self or not in room")
    if room.master != None and room.master != user:
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
    if room.master != None and room.master != user:
        raise helpers.Unauthorized("you are not the master")
    room.master = None
    return helpers.success()
