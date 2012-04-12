#!/usr/bin/env python
import yaml
import models

from flask import Flask, request, g, jsonify
from storm.locals import create_database, Store


app = Flask(__name__)


@app.before_request
def setup_request():
    # Read the configuration.
    stream = open('%s/config.yaml' % request.environ['UNISON_ROOT'])
    g.config = yaml.load(stream)
    # Set up the database.
    database = create_database(g.config['database']['string'])
    g.store = Store(database)


@app.route('/')
def hello_world():
    return 'Hello, Welcome to the API!'


@app.route('/users/<uuid>', methods=['PUT'])
def register(uuid):
    return """Register a user with the corresponding UUID.
        (Re)assign a nickname."""


@app.route('/users/<uuid>/room', methods=['PUT'])
def join_room(uuid):
    return """Join a room."""


@app.route('/users/<uuid>/room', methods=['DELETE'])
def leave_room(uuid):
    return """Leave a room."""


@app.route('/userlibs/<uuid>', methods=['PUT'])
def dump_library(uuid):
    return """Dump (create or replace) a user's library."""


@app.route('/userlibs/<uuid>/batch', methods=['POST'])
def update_library(uuid):
    return """Update (add, modify, delete) a user's library."""


@app.route('/rooms', methods=['GET'])
def list_rooms():
    """Get a list of rooms."""
    rooms = list()
    for room in g.store.find(models.Room):
        rooms.append({
          'name': room.name,
          'participants': room.users.count()
        })
    return jsonify(rooms=rooms)


@app.route('/rooms', methods=['POST'])
def create_room():
    """Create a new room."""
    room = models.Room()
    room.name = request.form['name']
    g.store.add(room)
    g.store.commit()
    return list_rooms()


@app.route('/rooms/<int:id>', methods=['GET'])
def get_room_info(id):
    return """Get infos about the specified room (including members, current
        track name, etc...), is there a DJ or not..."""


@app.route('/rooms/<int:id>', methods=['POST'])
def get_track(id):
    return """Get the next track."""


@app.route('/rooms/<int:id>/master', methods=['PUT'])
def set_master(id):
    return """Take the DJ spot (if it is available)."""


@app.route('/rooms/<int:id>/master', methods=['DELETE'])
def leave_master(id):
    return """Leave the DJ spot."""


if __name__ == '__main__':
    app.run()
