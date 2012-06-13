#!/usr/bin/env python
"""Library entry related views."""

import helpers
import hashlib
import json
import libunison.predict as predict
import pika

from constants import errors
from flask import Blueprint, request, g, jsonify
from libunison.models import User, Group, Track, LibEntry, GroupEvent


libentry_views = Blueprint('libentry_views', __name__)


def local_valid_entries(user):
    entrydict = dict()
    rows = g.store.find(LibEntry, (LibEntry.user == user)
            & LibEntry.is_local & LibEntry.is_valid)
    for lib_entry in rows:
        key = hashlib.sha1(lib_entry.track.artist.encode('utf-8')
                + lib_entry.track.title.encode('utf-8')
                + str(lib_entry.local_id)).digest()
        entrydict[key] = lib_entry
    return entrydict


def init_track(track):
    """Initialize a new track.

    To be used when creating a new track. In concrete terms, this function
    generates and sends the jobs that will fetch the track's tags and other
    information.
    """
    meta = {'artist': track.artist, 'title': track.title}
    tags_msg = json.dumps({
      'action': 'track-tags',
      'track': meta,
    })
    info_msg = json.dumps({
      'action': 'track-info',
      'track': meta,
    })
    # Set up the connection.
    queue = g.config['queue']['name']
    conn = pika.BlockingConnection(
            pika.ConnectionParameters(g.config['queue']['host']))
    channel = conn.channel()
    # Creates the queue if it doesn't exist yet.
    channel.queue_declare(queue=queue, durable=True)
    # Send the messages to the queue.
    channel.basic_publish(exchange='', routing_key=queue, body=tags_msg,
            properties=pika.BasicProperties(delivery_mode=2))
    channel.basic_publish(exchange='', routing_key=queue, body=info_msg,
            properties=pika.BasicProperties(delivery_mode=2))
    # Closing the connection flushes all the messages.
    conn.close()


def set_lib_entry(user, artist, title, local_id=None, rating=None):
    """Set a library entry for the user.

    This function sets a library entry for the (artist, title) pair. It takes
    care of:
    - invalidating the previous entry if there is one
    - creating a new track if it is the first time we encounte the (artist,
      title) pair
    """
    track = g.store.find(Track, (Track.artist == artist)
            & (Track.title == title)).one()
    if track is None:
        # First time that we encounter this track.
        track = Track(artist, title)
        g.store.add(track)
        # We need to commit *before* sending jobs to the last.fm queue.
        g.store.commit()
        init_track(track)
        entry = None
    else:
        # Track already in the system. Maybe the user even has an entry.
        entry = g.store.find(LibEntry, (LibEntry.user == user)
                & (LibEntry.track == track) & LibEntry.is_valid).one()
    if entry is not None and not entry.is_local and local_id is not None:
        # User already has a (non-local) entry. Just make it local.
        entry.is_local = True
        entry.local_id = local_id
    else:
        if entry is not None:
            # Invalidate the entry before creating a new one.
            entry.is_valid = False
        new_entry = LibEntry(user, track, is_valid=True)
        new_entry.is_local = local_id is not None
        new_entry.local_id = local_id
        new_entry.rating = rating
        g.store.add(new_entry)


def set_rating(user, artist, title, rating):
    """Insert a rating into the database.
    
    Helper function that handles the various cases that can arise, e.g. when a
    track is already in the user's library.
    """
    track = g.store.find(Track,
            (Track.artist == artist) & (Track.title == title)).one()
    if track is None:
        raise helpers.BadRequest(errors.INVALID_TRACK,
                "track not found")
    entry = g.store.find(LibEntry, (LibEntry.user == user)
            & (LibEntry.track == track) & LibEntry.is_valid).one()
    if entry is None:
        # First time we hear about this (user, track) pair.
        set_lib_entry(user, artist, title, rating=rating)
    elif entry.rating is None:
        # User has an entry for this track, but no rating yet.
        entry.rating = rating
    else:
        # Rating already present, we need to create a new entry.
        set_lib_entry(user, artist, title,
                local_id=entry.local_id, rating=rating)


@libentry_views.route('/<int:uid>', methods=['PUT'])
@helpers.authenticate(with_user=True)
def dump_library(user, uid):
    """Dump (create or replace) a user's library."""
    helpers.ensure_users_match(user, uid)
    current_entries = local_valid_entries(user)
    next_entries = set()
    for json_entry in request.form.getlist('entry'):
        try:
            entry = json.loads(json_entry)
            artist = entry['artist']
            title = entry['title']
            local_id = int(entry['local_id'])
        except:
            raise helpers.BadRequest(errors.INVALID_LIBENTRY,
                    "not a valid library entry")
        key = hashlib.sha1(artist.encode('utf-8')
                + title.encode('utf-8') + str(local_id)).digest()
        next_entries.add(key)
        if key not in current_entries:
            set_lib_entry(user, artist, title, local_id=local_id)
    # Invalidate entries that are not in the request.
    for key, entry in current_entries.iteritems():
        if key not in next_entries:
            entry.is_valid = False
    # Update the user's model.
    g.store.flush()
    predict.Model(user).generate(g.store)
    return helpers.success()


@libentry_views.route('/<int:uid>/batch', methods=['POST'])
@helpers.authenticate(with_user=True)
def update_library(user, uid):
    """Update (add or delete) a user's library."""
    helpers.ensure_users_match(user, uid)
    current_entries = local_valid_entries(user)
    for json_delta in request.form.getlist('delta'):
        try:
            delta = json.loads(json_delta)
            delta_type = delta['type']
            artist = delta['entry']['artist']
            title = delta['entry']['title']
            local_id = int(delta['entry']['local_id'])
        except:
            raise helpers.BadRequest(errors.INVALID_DELTA,
                    "not a valid library delta")
        key = hashlib.sha1(artist.encode('utf-8')
                + title.encode('utf-8') + str(local_id)).digest()
        if delta_type == 'PUT':
            if key not in current_entries:
                set_lib_entry(user, artist, title, local_id=local_id)
        elif delta_type == 'DELETE':
            if key in current_entries:
                current_entries[key].is_valid = False
        else:
            # Unknown delta type.
            raise helpers.BadRequest(errors.INVALID_DELTA,
                    "not a valid library delta")
    # Update the user's model.
    g.store.flush()
    predict.Model(user).generate(g.store)
    return helpers.success()


@libentry_views.route('/<int:uid>/ratings', methods=['GET'])
@helpers.authenticate(with_user=True)
def get_ratings(user, uid):
    """Get a list of ratings for the user."""
    helpers.ensure_users_match(user, uid)
    entries = g.store.find(LibEntry, (LibEntry.user == user)
            & (LibEntry.rating != None) & LibEntry.is_valid)
    ratings = list()
    for entry in entries:
        ratings.append({
            'artist': entry.track.artist,
            'title': entry.track.title,
            'local_id': entry.local_id,
            'rating': entry.rating,
        })
    return jsonify(ratings=ratings)


@libentry_views.route('/<int:uid>/ratings', methods=['POST'])
@helpers.authenticate(with_user=True)
def add_rating(user, uid):
    """Set a rating for the user."""
    helpers.ensure_users_match(user, uid)
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
    set_rating(user, artist, title, rating)
    return helpers.success()
