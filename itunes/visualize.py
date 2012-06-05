#!/usr/bin/env python

import argparse
import itertools
import libunison.utils as uutils
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

from db import *
from sklearn import mixture


DEFAULT_DB = 'gen/itunes.db'


def main(args):
    pts, labels = get_points(args.db, args.user)
    plot(pts, labels)
    

def make_ellipses(gmm, ax, nb):
    colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
    for n, color in enumerate(colors[:nb]):
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


def plot(points, labels):
    rows = itertools.izip(*points)
    x = next(rows)
    y = next(rows)
    fig = plt.figure()
    ax = fig.add_subplot(1, 1, 1)
    
    clf = mixture.GMM(n_components=3, covariance_type='diag')
    clf.fit(points)

    make_ellipses(clf, ax, 3)

    xx = np.linspace(-1.0, 1.0)
    yy = np.linspace(-1.0, 1.0)
    X, Y = np.meshgrid(xx, yy)
    XX = np.c_[X.ravel(), Y.ravel()]
    Z = np.log(-clf.eval(XX)[0])
    Z = Z.reshape(X.shape)

    CS = ax.contour(X, Y, Z)
    CB = plt.colorbar(CS, shrink=0.8, extend='both')

    #plt.xlabel('Dimension 1')
    #plt.ylabel('Dimension 2')
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
        print "--- points at this position:"
        print "\n".join(tracks)
    fig.canvas.mpl_connect('pick_event', onpick)
    plt.show()


def get_points(dbname, username):
    pts = list()
    labels = dict()
    # Initialize the user / track DB.
    store = Store(create_database('sqlite:%s' % dbname))
    user = store.find(User, User.name == username).one()
    if user is None:
        raise LookupError('username not found in database')
    for track in user.tracks:
        if track.features is not None:
            features = uutils.decode_features(track.features.encode('utf-8'))
            point = tuple(features[:2])
            pts.append(point)
            labels[point] = u"%s - %s" % (track.artist, track.title)
    return pts, labels


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('user', type=unicode)
    parser.add_argument('--db', default=DEFAULT_DB)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    main(args)
