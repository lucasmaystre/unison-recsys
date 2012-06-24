#!/usr/bin/env python

import argparse
import libunison.utils as uutils
import libunison.predict as predict

from libunison.models import User
from storm.locals import *


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('user', nargs='*', type=int)
    parser.add_argument('--null', action='store_true')
    parser.add_argument('--all', action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    store = uutils.get_store()
    users = set()
    for uid in args.user:
        user = store.get(User, uid)
        if user is not None:
            users.add(user)
    if args.all:
        users.update(store.find(User))
    elif args.null:
        users.update(store.find(User, User.model == None))
    for user in users:
        print "updating model for user %s..." % user.email
        model = predict.Model(user)
        model.generate(store)
        print "    ... %d components" % model.get_nb_components()
    store.commit()
