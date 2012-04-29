#!/usr/bin/env python

import base64
import functools
import libunison.password as password
import werkzeug.exceptions

from constants import errors
from flask import Response, jsonify, request, g
from libunison.models import User


def authenticate(with_user=False):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            if request.authorization is None:
                raise Unauthorized()
            try:
                email = base64.b64decode(
                        request.authorization.username).decode('utf-8')
                pw = base64.b64decode(
                        request.authorization.password).decode('utf-8')
            except:
                raise Unauthorized("could not decode email / password")
            user = g.store.find(User, User.email == email).one()
            if user is None:
                raise Unauthorized()
            if not password.verify(pw, user.password):
                raise Unauthorized()
            if with_user:
                return fn(user, *args, **kwargs)
            else:
                return fn(*args, **kwargs)
        return wrapper
    return decorator


def ensure_users_match(user, uid):
    if user.id != uid:
        raise Unauthorized()


def success():
    return jsonify(success=True)


class BadRequest(werkzeug.exceptions.BadRequest):
    def __init__(self, error, msg):
        super(BadRequest, self).__init__(msg)
        self.error = error
        self.msg = msg


class NotFound(werkzeug.exceptions.NotFound):
    def __init__(self, error, msg):
        super(NotFound, self).__init__(msg)
        self.error = error
        self.msg = msg


class Unauthorized(werkzeug.exceptions.Unauthorized):
    def __init__(self, msg='could not authenticate'):
        super(Unauthorized, self).__init__(msg)
        self.error = errors.UNAUTHORIZED
        self.msg = msg
