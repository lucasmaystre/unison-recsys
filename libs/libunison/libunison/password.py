#!/usr/bin/env python
"""Password hashing based on PBKDF2."""

import base64
import hashlib
import os

from pbkdf2 import PBKDF2


NB_ITERATIONS = 1000
HASH_LENGTH = 16  # In bytes.
HASH_FUNCTION = hashlib.sha256


def encrypt(password, key=None):
    # Password must be Unicode.
    assert isinstance(password, unicode)
    if key is None:
        key = os.urandom(HASH_LENGTH)
    mac = PBKDF2(password.decode('utf-8'), key, iterations=NB_ITERATIONS,
            digestmodule=HASH_FUNCTION).read(HASH_LENGTH)
    return u":".join([
      base64.b64encode(key),
      base64.b64encode(mac)
    ])


def verify(password, encrypted):
   key, mac = encrypted.split(':')
   raw_key = base64.b64decode(key)
   return encrypted == encrypt(password, key=raw_key)


def is_good_enough(password):
    # For the moment, we only the length.
    return len(password) >= 6
