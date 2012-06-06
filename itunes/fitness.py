#!/usr/bin/env python

import argparse
import json
import libunison.utils as uutils
import numpy as np
import matplotlib.pyplot as plt
import operator
import os.path
import re
import sys

from db import *
from math import log
from sklearn import mixture


DEFAULT_DB = 'gen/itunes.db'


def process(user):
    tracks = list()
    for track in user.tracks:
        if track.features is not None:
            features = uutils.decode_features(track.features.encode('utf-8'))
            tracks.append([5*x for x in features])
    for dim in range(2, 16) + [20, 25, 30, 40]:
        for k in range(1, 21):
            subset = [x[:dim] for x in tracks]
            pts = np.array(subset)
            clf = mixture.GMM(n_components=k, covariance_type='diag')
            clf.fit(pts)
            print ("dim = %d, k = %d, cov = diag, bic = %f, aic = %f, n = %d"
                    % (dim, k, clf.bic(pts), clf.aic(pts), len(tracks)))


def sort(f):
    regex = re.compile("dim = (?P<dim>\d+?), k = (?P<k>\d+?), "
            "cov = (?P<cov>diag|full), bic = (?P<bic>.+?), "
            "aic = (?P<aic>.+?), n = (?P<n>\d+)\n")
    results = list()
    for line in open(f):
        params = regex.match(line).groupdict()
        results.append([
          int(params['dim']),
          int(params['k']),
          float(params['bic']),
          float(params['aic']),
          int(params['n']),
        ])
    return results


def print_sorted(f):
    results = sort(f)
    for dim in range(2, 16) + [20, 25, 30, 40]:
        fct = lambda x: x[0] == dim and x[2] == cov
        subset = filter(fct, results)
        for crit in ['bic', 'aic']:
            print "dim: %d, crit: %s" % (dim, crit)
            for e in sorted(subset,
                    key=lambda x: x[3] if crit == 'bic' else x[4]):
                print "k = %s (bic: %f, aic: %f)" % (e[1], e[3], e[4])
            print


def plot(f, folder):
    results = sort(f)
    prefix = os.path.basename(f).split(".")[0]
    for dim in range(2, 16) + [20, 25, 30, 40]:
        a, b, c = list(), list(), list()
        for x in results:
            if x[0] == dim:
                a.append(x[2])
                b.append(x[2] + (x[1]-1)*x[1]*log(x[4]))
                c.append(x[2] + 99*x[1]*log(x[4]))
        for i, x in enumerate([a, b, c]):
            plt.plot(x)
            plt.ylabel("BIC value")
            plt.title("%d-dimensional embedding" % dim)
            # Save the plot.
            path = os.path.join(folder, '%s-%d-%d.png' % (prefix, dim, i))
            plt.savefig(path, format='png')
            plt.clf()            


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=DEFAULT_DB)
    parser.add_argument('action', choices=['compute', 'sort', 'plot'])
    parser.add_argument('what')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    if args.action == 'compute':
        store = Store(create_database('sqlite:%s' % args.db))
        user = store.find(User, User.name == unicode(args.what)).one()
        if user is None:
            raise LookupError('username not found in database')
        process(user)
    elif args.action == 'sort':
        print_sorted(args.what)
    elif args.action == 'plot':
        folder = os.path.abspath('./fig')
        if not os.path.exists(folder):
            os.makedirs(folder)
        plot(args.what, folder)
