#!/usr/bin/env python

import helpers
import yaml

from flask import Flask, request, g, Response, jsonify
from storm.locals import create_database, Store

# Blueprints.
from user_views import user_views
from room_views import room_views
from libentry_views import libentry_views


app = Flask(__name__)
app.register_blueprint(user_views, url_prefix='/users')
app.register_blueprint(room_views, url_prefix='/rooms')
app.register_blueprint(libentry_views, url_prefix='/libentries')


@app.before_request
def setup_request():
    # Read the configuration.
    stream = open('%s/config.yaml' % request.environ['UNISON_ROOT'])
    g.config = yaml.load(stream)
    # Set up the database.
    database = create_database(g.config['database']['string'])
    g.store = Store(database)


@app.after_request
def teardown_request(response):
    # Commit & close the database connection.
    g.store.commit()
    g.store.close()
    return response


@app.errorhandler(401)
def handle_unauthorized(error):
    if isinstance(error, helpers.Unauthorized):
        response = jsonify(error=error.error, message=error.message)
        response.status_code = 401
        response.headers = {'WWW-Authenticate': 'Basic realm="API Access"'}
        return response
    return "unauthorized", 401


@app.errorhandler(400)
def handle_bad_request(error):
    if isinstance(error, helpers.BadRequest):
        response = jsonify(error=error.error, message=error.message)
        response.status_code = 400
        return response
    return "bad request", 400


@app.errorhandler(404)
def handle_not_found(error):
    if isinstance(error, helpers.BadRequest):
        response = jsonify(error=error.error, message=error.message)
        response.status_code = 404
        return response
    return "not found", 404


@app.route('/')
@helpers.authenticate(with_user=True)
def root(user):
    return jsonify(user_id=user.id)


if __name__ == '__main__':
    app.run()
