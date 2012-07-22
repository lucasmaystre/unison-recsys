#!/usr/bin/env python

import argparse
import itertools
import libunison.utils as uutils
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import os.path
import sys

from db import *
from sklearn import mixture
from mpl_toolkits.mplot3d import Axes3D


DEFAULT_DB = 'gen/itunes.db'


def main(args):
    if args.action == '2d':
        pts, labels = get_points(args.db, args.user, start_dim=1)
        plot(pts, labels)
    elif args.action == 'monge':
        pts, _ = get_points(args.db, args.user, start_dim=1, nb_dim=3)
        folder = os.path.abspath(args.user)
        if not os.path.exists(folder):
            os.makedirs(folder)
        project3d(pts, folder)
    elif args.action == '3d':
        users = list()
        for user in args.users:
            pts, labels = get_points(args.db, user, start_dim=1, nb_dim=3)
            users.append((user, pts, labels))
        plot3d(users)
    

def make_ellipses(gmm, ax, nb):
    colors = ['r', 'y', 'b', 'c', 'm', 'g', 'k']
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

    #make_ellipses(clf, ax, 3)

    xx = np.linspace(-0.4, 0.4)
    yy = np.linspace(-0.4, 0.4)
    X, Y = np.meshgrid(xx, yy)
    XX = np.c_[X.ravel(), Y.ravel()]
    Z = np.log(-clf.eval(XX)[0])
    Z = Z.reshape(X.shape)

    CS = ax.contour(X, Y, Z)
    CB = plt.colorbar(CS, shrink=0.8, extend='both')

    plt.xlabel('Dimension 1')
    plt.ylabel('Dimension 2')
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
    plt.xlim(-0.35, 0.25)
    plt.ylim(-0.4, 0.4)
    #plt.savefig('scatter.png', format='png', dpi=300)
    plt.show()


def plot3d(users):
    colors = iter(['k', 'r', 'y', 'b', 'g', 'c', 'm'])
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    for name, points, labels in users:
        color = next(colors)
        rows = itertools.izip(*points)
        x = next(rows)
        y = next(rows)
        z = next(rows)
        ax.scatter(x, y, z, c=color)
    ax.set_xlabel('1st concept')
    ax.set_ylabel('2nd concept')
    ax.set_zlabel('3rd concept')
    #plt.savefig('3d.png', format='png', dpi=300)
    plt.show()


def project3d(points, folder):
    rows = itertools.izip(*points)
    x = next(rows)
    y = next(rows)
    z = next(rows)
    vmin = min(min(x), min(y), min(z)) - 0.01
    vmax = max(max(x), max(y), max(z)) + 0.01
    for plane, pair in enumerate([(y,x), (y,z), (x,z)], start=1):
        plt.title('Plane %d' %plane)
        plt.scatter(*pair, s=2)
        plt.xlim(vmin, vmax)
        plt.ylim(vmin, vmax)
        ax = plt.gca()
        ax.set_aspect(1)
        if plane == 1:
            ax.set_ylim(ax.get_ylim()[::-1])
        elif plane == 3:
            ax.set_xlim(ax.get_xlim()[::-1])
        #plt.axis('equal')
        path = os.path.join(folder, 'plane-%d.png' % plane)
        plt.savefig(path, format='png')
        plt.clf()


def get_points(dbname, username, start_dim=0, nb_dim=2):
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
            point = tuple(features[start_dim:start_dim+nb_dim])
            pts.append(point)
            labels[point] = u"%s - %s" % (track.artist, track.title)
    return pts, labels


def _parse_args():
    actions = ['2d', '3d', 'monge']
    global_parser = argparse.ArgumentParser()
    global_parser.add_argument('action', choices=actions)
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default=DEFAULT_DB)
    args = global_parser.parse_args(args=sys.argv[1:2])
    if args.action == '2d':
        parser.add_argument('user', type=unicode)
    elif args.action == '3d':
        parser.add_argument('users', nargs='+', type=unicode)
    elif args.action == 'monge':
        parser.add_argument('user', type=unicode)
    parser.parse_args(args=sys.argv[2:], namespace=args)
    return args


if __name__ == '__main__':
    args = _parse_args()
    main(args)
