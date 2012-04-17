#!/usr/bin/env python
"""Quick and dirty plotting script for classification results."""

import argparse
import json
import matplotlib.pyplot as plt
import numpy as np
import os.path


def plot(data, name, save):
    labels = list()
    means = list()
    std = list()
    for label, values in data.iteritems():
        labels.append(label)
        means.append(100*values[0])
        std.append(100*values[1])

    ind = np.arange(len(labels))  # the x locations for the groups
    width = 0.6  # the width of the bars: can also be len(x) sequence

    p1 = plt.bar(ind, means, width, color='r', yerr=std)
    plt.ylabel('Score')
    plt.title('User %s' % name)
    plt.xticks(ind+width/2., labels)
    plt.yticks(np.arange(0,101,10))
    plt.legend( (p1[0],), ('Classifier performance',) )
    plt.axhline(y=50)  # Horizontal line indicating random choice.

    if save is None:
        plt.show()
    else:
        path = os.path.join(save, '%s.eps' % name)
        plt.savefig(path, format='eps')
    plt.clf()


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file', nargs='+')
    parser.add_argument('--save')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    for f in args.file:
        data = json.loads(open(f).read())
        name = os.path.basename(f)
        plot(data, name, args.save)
