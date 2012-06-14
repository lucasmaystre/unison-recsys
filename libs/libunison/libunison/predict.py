#!/usr/bin/env python

import numpy as np
import sklearn.mixture
import utils
import math
import pickle

from operator import itemgetter, mul
from models import *


DIMENSIONS = 5
SCALE = 5


class Model(object):

    K_MAX = 10
    MIN_COVAR = 0.001

    def __init__(self, user):
        self._user = user
        if user.model is not None:
            self._gmm = pickle.loads(user.model.encode('utf-8'))
        else:
            self._gmm = None

    def generate(self, store):
        points = get_points(self._user, store)
        k_max = min(self.K_MAX, len(points) / (2 * DIMENSIONS))
        if k_max < 1:
            self._user.model = None
            self._gmm = None
            return
        candidates = list()
        for k in range(1, k_max+1):
            gmm = sklearn.mixture.GMM(n_components=k, covariance_type='full',
                    min_covar=self.MIN_COVAR)
            gmm.fit(points)
            candidates.append((gmm, gmm.bic(points)))
        self._gmm, bic = min(candidates, key=itemgetter(1))
        self._user.model = unicode(pickle.dumps(self._gmm))
        store.flush()

    def is_nontrivial(self):
        return self._gmm is not None

    def get_nb_components(self):
        if not self.is_nontrivial():
            return 0
        return self._gmm.n_components

    def score(self, points):
        if not self.is_nontrivial():
            return None
        return [math.exp(x) for x in self._gmm.score(points)]


def get_points(user, store):
    points = list()
    rows = store.find(LibEntry, (LibEntry.user == user)
            & LibEntry.is_local & LibEntry.is_valid)
    for row in rows:
        point = get_point(row.track)
        if point is not None:
            points.append(point)
    return np.array(points)


def get_point(track):
    if track.features is not None:
        features = utils.decode_features(track.features)
        return [x*SCALE for x in features[:DIMENSIONS]]
    return None


def aggregate(ratings, mode='mult'):
    aggregate = list()
    for track_ratings in zip(*ratings):
        if mode == 'mult':
            track_aggregate = reduce(mul, track_ratings)
        elif mode == 'add':
            track_aggregate = sum(track_ratings)
        else:
            raise ValueError('mode unknown')
        aggregate.append(track_aggregate)
    return aggregate
