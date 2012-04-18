#!/usr/bin/env python
"""
Last.fm loved / banned songs classification.

To use the homebrewed Gaussian naive Bayes classifier, a typical session looks
like this:

    # Merge the three databases and generate feature vectors.
    ./classifier.py genfeat USERNAME 50
    # Generate a test set.
    ./sample.py 0.2 gen/features.dat > test.dat
    # Take the remaining items for the train set.
    comm -23 <(sort gen/features.dat) <(sort test.dat) > train.dat
    # Build the model.
    ./classifier.py genmodel train.dat 50
    # Classify the test tracks.
    ./classifier.py classify gen/model.dat test.dat 
"""

import argparse
import json
import numpy as np
import random
import sqlite3
import struct
import sys

from math import exp, log, log1p, sqrt
from sklearn.naive_bayes import GaussianNB
from sklearn.svm import SVC, NuSVC
from libunison.utils import GEN_ROOT, memo, get_vector


DEFAULT_TRACK_DB = '%s/trackdata.db' % GEN_ROOT
DEFAULT_USER_DB = '%s/userdata.db' % GEN_ROOT
DEFAULT_TAG_DB = '%s/d500.db' % GEN_ROOT
DEFAULT_FEATURES_FILE = '%s/features.dat' % GEN_ROOT
DEFAULT_MODEL_FILE = '%s/model.dat' % GEN_ROOT

STRUCT_FLOAT = struct.Struct('!f')

# SQL queries for the user database.
SELECT_USERID = "SELECT ROWID FROM users WHERE name = ?"
SELECT_TRACKS = "SELECT artist, title, status FROM tracks WHERE user = ?"

# SQL queries for the tracks database.
SELECT_TAGS = "SELECT tags FROM tracks WHERE artist = ? AND title = ?"

# Related to classification statistics.
TRAIN_TEST_RATIO = 0.2
CLF_ITERATIONS = 100
CLF_DIMENSIONS = 50


def encode(features):
    encoded = ''
    for val in features:
        encoded += STRUCT_FLOAT.pack(val).encode('hex_codec')
    return encoded


def decode(encoded):
    features = list()
    for i in xrange(0, len(encoded), 8):
        raw = encoded[i:i+8].decode('hex_codec')
        features.append(STRUCT_FLOAT.unpack(raw)[0])
    return features


def gen_features(username, userdb, trackdb, tagdb, dim, out):
    f = open(out, 'w')
    tagf = make_tag_features(tagdb)
    # Get the user's ROWID.
    user = userdb.execute(SELECT_USERID, (username,)).fetchone()
    # Iterate over all the tracks of that user.
    for row in userdb.execute(SELECT_TRACKS, (user[0],)):
        track = trackdb.execute(SELECT_TAGS, (row[0], row[1])).fetchone()
        if track is None:
            # Track was not found. Ignore it.
            continue
        features = track_features(json.loads(track[0]), tagf, dim)
        if features is None:
            # Features couldn't be extracted. Ignore it.
            continue
        f.write("%s|%s\n" % (row[2], encode(features)))
    f.close()


#_tag_freq = dict()
def track_features(tags, tag_features, dimensions):
    #global _tag_freq
    vector = [0] * dimensions
    total = 0
    for tag, count in tags:
        #_tag_freq[tag] = _tag_freq.get(tag, 0) + int(count)
        curr, gw = tag_features(tag)
        if curr is None:
            continue
        weight = gw * log1p(float(count)) / log(2)
        vector = [(weight*x + y) for x, y in zip(curr, vector)]
        total += weight
    # Normalizing the vector would make us lose independence of features.
    # However, we should still compensate for the document's length.
    return tuple([x / total for x in vector]) if total > 0 else None


def make_tag_features(conn):
    @memo
    def tag_features(tag):
        return get_vector(conn, tag, normalize=False)
    return tag_features


def gen_model(trainset, dim, out):
    f = open(out, 'w')
    lines = open(trainset).readlines()
    total = dict()
    squares = dict()
    nb_samples = dict()
    for status in ('loved', 'banned'):
        total[status] = [0] * dim
        squares[status] = [0] * dim
        nb_samples[status] = 0
    for line in lines:
        status, encoded = line.strip().split('|')
        example = decode(encoded)
        for i, val in enumerate(example):
            total[status][i] += val
            squares[status][i] += val * val
        nb_samples[status] += 1
    for status in ('loved', 'banned'):
        encoded = ''
        for i in xrange(dim):
            mu = total[status][i] / nb_samples[status]
            sigma = sqrt(squares[status][i] / nb_samples[status] - mu * mu)
            encoded += encode([mu, sigma])
        f.write("%s\n" % encoded)
    f.close()


def test_classifier(data, ratio, clf):
    size = int(ratio * len(data))
    scores = list()
    for i in xrange(CLF_ITERATIONS):
        # Separate data into test set / train set.
        random.shuffle(data)
        test = data[:size]
        train = data[size:]
        # Separate features from class labels.
        items, labels = zip(*train)
        t_items, t_labels = zip(*test)
        score = clf.fit(items, labels).score(t_items, t_labels)
        scores.append(score)
    res = np.array(scores)
    return res.mean(), res.std()


def test(features, dim):
    result = dict()
    data = list()
    for line in open(features):
        status, encoded = line.strip().split('|')
        item = decode(encoded)[:dim]
        label = 0 if status == 'banned' else 1
        data.append((item, label))
    # List of classifiers we want to test.
    classifiers = {
      'bayes': GaussianNB(),
      'svc-linear': SVC(kernel='linear', C=256, scale_C=False),
      'svc-rbf': SVC(kernel='rbf', C=256, gamma=1, scale_C=False),
      'nusvc-linear': NuSVC(kernel='linear', nu=0.8),
      'nusvc-rbf': NuSVC(kernel='rbf', nu=0.8, gamma=1),
    }
    for name, clf in classifiers.iteritems():
        try:
            print 'testing classifier %s' % name
            result[name] = test_classifier(data, TRAIN_TEST_RATIO, clf)
        except ValueError:
            # Thrown sometimes by NuSVC, when nu is infeasible.
            continue
    print json.dumps(result)


def classify(model, testset):
    params = dict()
    f = open(model)
    for status in ('loved', 'banned'):
        raw = decode(f.readline().strip())
        params[status] = [raw[i:i+2] for i in xrange(0, len(raw), 2)]
    successes = 0
    total = 0
    loved = 0
    for line in open(testset):
        true_status, encoded = line.strip().split('|')
        example = decode(encoded)
        score = dict()
        for status in ('loved', 'banned'):
            score[status] = 0
            for i, val in enumerate(example):
                score[status] += log(gauss_pdf(val, *params[status][i]))
        if score['loved'] > score['banned']:
            loved += 1
            if true_status == 'loved':
                successes += 1
        else:
            if true_status == 'banned':
                successes += 1
        total += 1
    print "total:     %d" % total
    print "successes: %d" % successes
    print "accuracy:  %.2f" % (100.0 * successes / total)
    print "loved:     %d" % loved



def gauss_pdf(x, mu, sigma):
    val = (1.0 / sigma) * exp(
            -1.0  * (x - mu) * (x - mu) / (2 * sigma * sigma))
    # Small hack because often we have extreme values...
    return max(val, 1e-99)


def _parse_args():
    actions = ['genfeat', 'genmodel', 'classify', 'sklearn']
    global_parser = argparse.ArgumentParser()
    global_parser.add_argument('action', choices=actions)
    args = global_parser.parse_args(args=sys.argv[1:2])
    if args.action == 'genfeat':
        parser = argparse.ArgumentParser()
        parser.add_argument('--user-db', default=DEFAULT_USER_DB)
        parser.add_argument('--track-db', default=DEFAULT_TRACK_DB)
        parser.add_argument('--tag-db', default=DEFAULT_TAG_DB)
        parser.add_argument('--out', default=DEFAULT_FEATURES_FILE)
        parser.add_argument('username')
        parser.add_argument('dimensions', type=int)
        parser.parse_args(args=sys.argv[2:], namespace=args)
    elif args.action == 'genmodel':
        parser = argparse.ArgumentParser()
        parser.add_argument('--out', default=DEFAULT_MODEL_FILE)
        parser.add_argument('trainset')
        parser.add_argument('dimensions', type=int)
        parser.parse_args(args=sys.argv[2:], namespace=args)
    elif args.action == 'classify':
        parser = argparse.ArgumentParser()
        parser.add_argument('model')
        parser.add_argument('testset')
        parser.parse_args(args=sys.argv[2:], namespace=args)
    elif args.action == 'sklearn':
        parser = argparse.ArgumentParser()
        parser.add_argument('features')
        parser.add_argument('--dimensions', type=int, default=CLF_DIMENSIONS)
        parser.parse_args(args=sys.argv[2:], namespace=args)
    return args


if __name__ == '__main__':
    args = _parse_args()
    if args.action == 'genfeat':
        gen_features(
            username = args.username,
            userdb = sqlite3.connect(args.user_db),
            trackdb = sqlite3.connect(args.track_db),
            tagdb = sqlite3.connect(args.tag_db),
            dim = args.dimensions,
            out = args.out)
        #for tag in sorted(_tag_freq, key=_tag_freq.get, reverse=True):
        #    if _tag_freq[tag] > 10:
        #        print tag, _tag_freq[tag]
    elif args.action == 'genmodel':
        gen_model(args.trainset, args.dimensions, args.out)
    elif args.action == 'classify':
        classify(args.model, args.testset)
    elif args.action == 'sklearn':
        test(args.features, args.dimensions)
