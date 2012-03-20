#!/usr/bin/env python
import sys
import json


DATASET_ROOT = './data/lastfm_raw'
DEFAULT_STR = '<unknown>'


def pretty_print(info):
    print "Artist: %s" % info.get('artist', DEFAULT_STR)
    print "Title:  %s" % info.get('title', DEFAULT_STR)
    if len(info.get('tags', [])) > 0:
        print "\n", "Tags:"
        for tag in info['tags']:
            print "- %s (%s)" % tuple(tag)


def main():
    if len(sys.argv) != 2:
        # Script should be called with a single argument: the track id.
        print "usage: %s tid" % sys.argv[0]
        sys.exit(0)
    tid = sys.argv[1]
    if len(tid) != 18 or tid != tid.upper() or tid[:2] != 'TR':
        # Track id has not the proper format (TRxxxxxxxxxxxxxxxx).
        print "Invalid tid."
        sys.exit(1)
    path = '%s/%s/%s/%s/%s.json' % (DATASET_ROOT, tid[2], tid[3], tid[4], tid)
    try:
        data = open(path).read()
    except IOError:
        # If we fail, it probably means we don't have this tid.
        print "Could not find specified tid (%s)." % tid
        sys.exit(1)
    # If we made it all the way through, we should be good to go :)
    pretty_print(json.loads(data))



if __name__ == '__main__':
    main()
