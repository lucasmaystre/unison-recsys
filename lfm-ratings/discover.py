#!/usr/bin/env python

import argparse
import math
import re
import sys
import urllib2


RE_USER = re.compile('href="/user/(?P<user>[^/]+?)"')
RE_NB_FRIENDS = re.compile('<h1>Friends \((?P<nb>\d+)\)</h1>')

ACTIVE_URL = 'http://www.last.fm/community/users/active?page=%d'
FRIENDS_URL = 'http://www.last.fm/user/%s/friends?page=%d'


def scrape_users(page):
    """Scrape all the usernames in a page."""
    return set([match.group('user') for match in RE_USER.finditer(page)])


def get_friends(user):
    """Get all friends of a user."""
    url = FRIENDS_URL % (user, 1)
    try:
        page = urllib2.urlopen(url).read()
    except urllib2.URLError as ue:
        print >> sys.stderr, "could not open URL: %s" % url
        return set()
    match = RE_NB_FRIENDS.search(page);
    if match is None:
        print >> sys.stderr, "could not find number of friends"
        return set()
    nb_pages = math.ceil(int(match.group('nb')) / 20)
    friends = scrape_users(page)
    for i in xrange(2, int(nb_pages) + 1):
        try:
            url = FRIENDS_URL % (user, i)
            page = urllib2.urlopen(url).read()
        except urllib2.URLError as ue:
            print >> sys.stderr, "could not open URL: %s" % url
            continue
        friends |= scrape_users(page)
    return friends


def get_active():
    """Get all users that are on the 'active' page."""
    active = list()
    for i in xrange(1, 11):
        try:
            url = ACTIVE_URL % i
            page = urllib2.urlopen(url).read()
        except urllib2.URLError as ue:
            print >> sys.stderr, "could not open URL: %s" % url
            continue
        active.extend(scrape_users(page))
    return set(active)


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--active', action='store_true', default=False)
    parser.add_argument('--friends')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    if args.active:
        for user in get_active():
            print user
    if args.friends is not None:
        for line in open(args.friends):
            user = line.strip()
            print >> sys.stderr, "processing user '%s'..." % user
            for friend in get_friends(user):
                print friend
