#!/usr/bin/env python

import argparse
import datetime
import time
import libunison.utils as uutils

from libunison.models import User, GroupEvent, Group
from storm.locals import *
from storm.expr import Desc


def cleanup(interval, verbose):
    thresh = datetime.datetime.fromtimestamp(
            time.time() - interval * 60 * 60)
    store = uutils.get_store()
    for group in store.find(Group, Group.is_active == True):
        # Iterate over all active groups.
        last_event = store.find(GroupEvent, GroupEvent.group
                == group).order_by(Desc(GroupEvent.created)).first()
        if (last_event is None and group.created < thresh
                or last_event is not None and last_event.created < thresh):
            # Group is old and has no event, or last event is old.
            if verbose:
                print "deactivating group %d (%s)" % (group.id, group.name)
            group.is_active = False
            for user in group.users:
                user.group = None
    store.commit()


def _parse_args():
    parser = argparse.ArgumentParser()
    # Cutoff interval, number of hours since last event in group.
    parser.add_argument('interval', type=int)
    parser.add_argument('--verbose', action='store_true')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    cleanup(args.interval, args.verbose)
