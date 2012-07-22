#!/usr/bin/env python

import argparse
import itertools
import libunison.predict as predict
import libunison.utils as uutils
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import sklearn
import sys

from libunison.models import User, LibEntry
from mpl_toolkits.mplot3d import Axes3D
from operator import itemgetter
from storm.locals import *

K_MAX = 10

def get_points(uid, store, start_dim=0, nb_dim=2):
    pts = list()
    labels = dict()
    user = store.get(User, uid)
    if user is None:
        raise LookupError('uid %d not found in database' % uid)
    entries = store.find(LibEntry, (LibEntry.user == user)
            & (LibEntry.is_local == True) & (LibEntry.is_valid == True))
    for entry in entries:
        track = entry.track
        if track.features is not None:
            features = uutils.decode_features(track.features)
            point = tuple(features[start_dim:start_dim+nb_dim])
            pts.append(point)
            labels[point] = u"%s - %s" % (track.artist, track.title)
    return pts, labels


def get_model(points, dim=2):
    pts = np.array(points)
    k_max = min(K_MAX, len(pts) / (2 * dim))
    if k_max < 1:
        return None
    candidates = list()
    for k in range(1, k_max+1):
        gmm = sklearn.mixture.GMM(n_components=k, covariance_type='full')
        gmm.fit(pts)
        candidates.append((gmm, gmm.aic(pts)))
    model, bic = min(candidates, key=itemgetter(1))
    return model


def make_ellipses(gmm, ax):
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
    for n, color in enumerate(colors[:gmm.n_components]):
        v, w = np.linalg.eigh(gmm._get_covars()[n][:2, :2])
        u = w[0] / np.linalg.norm(w[0])
        angle = np.arctan2(u[1], u[0])
        angle = 180 * angle / np.pi  # convert to degrees
        v *= 19
        ell = mpl.patches.Ellipse(gmm.means_[n, :2], v[0], v[1],
                                  180 + angle, color=color)
        ell.set_clip_box(ax.bbox)
        ell.set_alpha(0.5)
        ax.add_artist(ell)


def make_contour(gmm, ax):
    # Contour plot
    xx = np.linspace(-0.5, 0.5)
    yy = np.linspace(-0.5, 0.5)
    X, Y = np.meshgrid(xx, yy)
    XX = np.c_[X.ravel(), Y.ravel()]
    Z = np.log(-gmm.eval(XX)[0])
    Z = Z.reshape(X.shape)
    CS = ax.contour(X, Y, Z)
    CB = plt.colorbar(CS, shrink=0.8, extend='both')


def plot(uid, store, start_dim=0, contour=False, ellipses=False):
    points, labels = get_points(uid, store, start_dim)
    model = get_model(points)
    rows = itertools.izip(*points)
    x = next(rows)
    y = next(rows)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    if ellipses:
        make_ellipses(model, ax)
    if contour:
        make_contour(model, ax)
    sc = ax.scatter(x, y, 2, picker=True)
    plt.title('2-dimensional embedding')
    tbox = fig.text(0.15, 0.12, 'click on a point', va='bottom', ha='left', axes=ax,
            bbox=dict(facecolor='red', alpha=0.5))
    def onpick(event):
        id = event.ind
        tracks = list()
        for a, b in zip(np.take(x, id), np.take(y, id)):
            tracks.append(labels.get((a, b)))
        tbox.set_text("\n".join(tracks))
        fig.canvas.draw()
    fig.canvas.mpl_connect('pick_event', onpick)
    plt.show()


def compare(uids, store, start_dim=0):
    # Get the points.
    users = list()
    for uid in uids:
        pts, labels = get_points(uid, store, start_dim, nb_dim=3)
        users.append((uid, pts))
    # Plot them.
    colors = iter(['k', 'r', 'y', 'b', 'g', 'c', 'm'])
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    for uid, points in users:
        color = next(colors)
        rows = itertools.izip(*points)
        x = next(rows)
        y = next(rows)
        z = next(rows)
        ax.scatter(x, y, z, c=color)
    ax.set_xlabel('1st concept')
    ax.set_ylabel('2nd concept')
    ax.set_zlabel('3rd concept')
    #ax.view_init(30, 30)
    #plt.savefig('libs.png', format='png', dpi=300)
    plt.show()


def _parse_args():
    actions = ['plot', 'compare']
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=actions)
    args = parser.parse_args(args=sys.argv[1:2])
    # Action-specific argument parsing.
    parser = argparse.ArgumentParser()
    if args.action == 'plot':
        parser.add_argument('user', type=int)
        parser.add_argument('--start-dim', type=int, default=0)
        parser.add_argument('--contour', action='store_true')
        parser.add_argument('--ellipses', action='store_true')
    elif args.action == 'compare':
        parser.add_argument('user', nargs='+', type=int)
        parser.add_argument('--start-dim', type=int, default=0)
    parser.parse_args(args=sys.argv[2:], namespace=args)
    return args


if __name__ == '__main__':
    args = _parse_args()
    store = uutils.get_store()
    if args.action == 'plot':
        plot(args.user, store, start_dim=args.start_dim,
                ellipses=args.ellipses, contour=args.contour)
    elif args.action == 'compare':
        compare(args.user, store, start_dim=args.start_dim)
