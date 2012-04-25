#!/usr/bin/env python
import yaml

from functools import wraps
from flask import Flask, Response, request, g, jsonify
from libunison.models import User, Room, Track, LibEntry, Transaction
from storm.locals import create_database, Store


app = Flask(__name__)


def requires_user(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            uuid = request.headers['Unison-UUID']
        except KeyError:
            return Response("Unison-UUID header is missing.", 401)
        # Note: here we could fail if the header value is not ASCII.
        user = g.store.get(User, uuid.decode('ascii'))
        if user is None:
            return Response("UUID is incorrect.", 401)
        return f(user, *args, **kwargs)
    return decorated


@app.before_request
def setup_request():
    # Read the configuration.
    stream = open('%s/config.yaml' % request.environ['UNISON_ROOT'])
    g.config = yaml.load(stream)
    # Set up the database.
    database = create_database(g.config['database']['string'])
    g.store = Store(database)


@app.route('/')
@requires_user
def hello_world(user):
    return 'Hello %s, Welcome to the API!' % user.nickname


@app.route('/users/<uuid>', methods=['PUT'])
def register(uuid):
    """Register a user with the corresponding UUID. (Re)assign a nickname."""
    user = g.store.get(User, uuid)
    if user is None:
        # We're dealing with a new user.
        user = User()
        user.uuid = uuid
        g.store.add(user)
    user.nickname = request.form['nickname']
    g.store.commit()
    # Just return the status code.
    return None, 200


@app.route('/users/<uuid>/room', methods=['PUT'])
@requires_user
def join_room(user, uuid):
    """Join a room."""
    if user.uuid != uuid:
        return "UUIDs don't match", 401
    try:
        room_id = int(request.form['room'])
    except:
        return "Cannot parse room ID.", 400
    if g.store.get(Room, room_id) is None:
        return "Room doesn't exist.", 400
    user.room_id = room_id
    g.store.commit()
    return None, 200


@app.route('/users/<uuid>/room', methods=['DELETE'])
@requires_user
def leave_room(user, uuid):
    """Leave a room."""
    if user.uuid != uuid:
        return "UUIDs don't match", 401
    user.room = None
    g.store.commit()
    return None, 200


@app.route('/libentries/<uuid>', methods=['PUT'])
@requires_user
def dump_library(user, uuid):
    """Dump (create or replace) a user's library."""
    if user.uuid != uuid:
        return "UUIDs don't match", 401
    # Not yet implemented.
    return "Come back soon!", 501


@app.route('/libentries/<uuid>/batch', methods=['POST'])
@requires_user
def update_library(user, uuid):
    """Update (add, modify, delete) a user's library."""
    if user.uuid != uuid:
        return "UUIDs don't match", 401
    # Not yet implemented.
    return "Come back soon!", 501


@app.route('/rooms', methods=['GET'])
@requires_user
def list_rooms(user):
    """Get a list of rooms."""
    rooms = list()
    for room in g.store.find(Room):
        rooms.append({
          'name': room.name,
          'participants': room.users.count()
        })
    return jsonify(rooms=rooms)


@app.route('/rooms', methods=['POST'])
@requires_user
def create_room(user):
    """Create a new room."""
    room = Room()
    room.name = request.form['name']
    g.store.add(room)
    g.store.commit()
    return list_rooms()


@app.route('/rooms/<int:id>', methods=['GET'])
@requires_user
def get_room_info(user, id):
    """Get infos about the specified room.

    Including members, current track name, etc...), is there a DJ or not...
    """
    # Not yet implemented.
    return "Come back soon!", 501


@app.route('/rooms/<int:id>', methods=['POST'])
@requires_user
def get_track(user, id):
    """Get the next track."""
    # Not yet implemented.
    return "Come back soon!", 501


@app.route('/rooms/<int:id>/master', methods=['PUT'])
@requires_user
def set_master(user, id):
    """Take the DJ spot (if it is available)."""
    try:
        uuid = request.form['user']
    except KeyError:
        return "Cannot parse user.", 401
    if user.uuid != uuid:
        return "UUIDs don't match", 401
    if user.room_id != id:
        return "You're not even in this room.", 400
    if user.room.master != None:
        return "DJ spot already filled, sorry.", 400
    # Set the user as his room's DJ.
    user.room.master = user
    g.store.commit()
    return None, 200


@app.route('/rooms/<int:id>/master', methods=['DELETE'])
@requires_user
def leave_master(user, id):
    """Leave the DJ spot."""
    if user.room_id != id:
        return "You're not even in this room.", 400
    if user.room.master_id != user.uuid:
        return "You aren't the DJ anyways.", 400
    # Remove the user's room's DJ.
    user.room.master = None
    g.store.commit()
    return None, 200


if __name__ == '__main__':
    app.run()
