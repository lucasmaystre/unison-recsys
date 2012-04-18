#!/usr/bin/env python
"""Write a tag-track matrix for use with SVDLIBC.

This script writes out a tag-track matrix from the lastfm_tags.db sqlite
database. We use the sparse binary matrix format (SVD_F_SB), as defined in the
SVDLIBC docs:

    numRows numCols totalNonZeroValues
    for each column:
      numNonZeroValues
      for each non-zero value in the column:
        rowIndex value
    
    All values are 4-byte integers except value, which is a 4-byte float. All
    are in network byte order.

The entries in the tag-track matrix are weighted according to the Log-Entropy
weighting scheme. See for example:

    Dumais, S., "Improving the retrieval of information from external sources",
    in Behavior Research Methods, 1991
"""

import argparse
import codecs
import marshal
import os
import sqlite3
import struct

from math import log, log1p
from libunison.utils import (MATRIX_PATH, TAGS_PATH, WEIGHTS_PATH,
        dump_tags, dump_weights, create_tree)


# SQL queries.
QUERY_ALL_TRACKS = "SELECT tid FROM tids"
QUERY_TAGS_FOR_TRACK = ("SELECT tags.tag, tid_tag.val FROM tags, tid_tag, tids "
        + "WHERE tags.ROWID = tid_tag.tag "
        + "AND tid_tag.tid = tids.ROWID "
        + "AND tids.tid = ?")

# Compiled Struct objects to avoid reparsing the format everytime.
STRUCT_COL_HEADER = struct.Struct("!l")
STRUCT_COL_ENTRY = struct.Struct("!lf")

TMP_FILE = '/tmp/genmat.mat'
LOG2 = log(2)


def generate_matrix(tags_dict, db, path, max_nb=-1):
    """Write out a tag-track matrix in the sparse binary matrix format.

    Fetches the tracks and tags from the SQLite database. Restricts the tags to
    those in 'tags_dict', and optionally stops after 'max_nb' tracks.

    Returns the list of global weights used to generate the matrix.
    """
    mat_file = open(path, 'wb')
    tmp_file = open(TMP_FILE, 'w+b')
    update_header(tmp_file)
    # Initialize the matrix header values.
    nb_rows = len(tags_dict)  # Number of tags.
    nb_cols = 0  # Will be equal to the number of tracks.
    nb_non_zero = 0  # Total number of nonzero values.
    # Initialize the two running sums needed for the global weighting.
    tf_sum = [0] * len(tags_dict)
    log_sum = [0] * len(tags_dict)

    # Set up the connection to the database, and create two cursors.
    conn = sqlite3.connect(db)
    tracks_cursor = conn.cursor()
    tags_cursor = conn.cursor()
    # Iterate over all tracks.
    tracks_cursor.execute(QUERY_ALL_TRACKS)
    for track in tracks_cursor:
        column = list()
        # Iterate over the associated tags.
        tags_cursor.execute(QUERY_TAGS_FOR_TRACK, (track[0],))
        for tag in tags_cursor:
            name = tag[0]
            freq = tag[1]
            if name in tags_dict and freq > 0:
                # Local weight is log2(1 + tf)
                entry = (tags_dict[name], log1p(freq) / LOG2)
                tf_sum[tags_dict[name]] += freq
                log_sum[tags_dict[name]] += freq * (log(freq) / LOG2)
                column.append(entry)
        if len(column) == 0:
            # The track results in an all-zero column. Skip it.
            continue
        # Update track count and non-zero value count.
        nb_cols += 1
        nb_non_zero += len(column)
        append_column(tmp_file, column)
        if max_nb > 0 and nb_cols >= max_nb:
            break  # We're done, we have enough tracks.
    # We need to update the header with the correct values.
    update_header(tmp_file, rows=nb_rows, cols=nb_cols, total=nb_non_zero)
    # Apply the global weights to the matrix entries.
    weights = compute_weights(nb_cols, tf_sum, log_sum)
    apply_weights(tmp_file, mat_file, weights)
    # We're done! Yay!
    tmp_file.close()
    os.remove(TMP_FILE)
    mat_file.close()
    return weights


def update_header(mfile, rows=0, cols=0, total=0):
    """Update the header for a matrix in sparse binary format.

    The file 'mfile' has to be opened with the flags r+b or wb to allow writing
    anywhere in the file.
    """
    # Exclamation point (!) means network byte order (big endian).
    data = struct.pack('!lll', rows, cols, total)
    mfile.seek(0)
    mfile.write(data)


def append_column(mfile, column):
    """Append a new column to a sparse binary matrix."""
    mfile.seek(0, os.SEEK_END)  # Append to the file.
    mfile.write(STRUCT_COL_HEADER.pack(len(column)))
    for entry in column:
        mfile.write(STRUCT_COL_ENTRY.pack(*entry))


def compute_weights(nb_tracks, gf, log_sum):
    """Compute the global weights (entropy strategy)."""
    weights = [0] * len(gf)
    # Normalization factor.
    c = 1 / (log(nb_tracks) / LOG2)
    for i in xrange(len(gf)):
        if gf[i] > 0:
            # Entropy-based, i.e. w[i] = 1 - H(Track | Tag = i) / H(Track)
            entropy = (gf[i] * log(gf[i]) / LOG2) - log_sum[i]
            weights[i] = 1 - (c / gf[i]) * entropy
    return weights


def apply_weights(tmp_file, mat_file, weights):
    """Rewrite the matrix by applying the global weights.

    Global weights cannot be computed prior to writing the matrix. For this
    reason once the matrix is complete it has to be rewritten.
    """
    tmp_file.seek(0)
    mat_file.seek(0)
    # Copy (rewrite) the matrix with the global weights.
    header = tmp_file.read(3 * 4)
    mat_file.write(header)
    rows, cols, total = struct.unpack('!lll', header)
    for i in xrange(cols):
        # Iterate over tracks (columns)
        col_header = tmp_file.read(4)
        mat_file.write(col_header)
        nb_val, = STRUCT_COL_HEADER.unpack(col_header)
        for j in xrange(nb_val):
            # Iterate over non zero entries of the track.
            index, val = STRUCT_COL_ENTRY.unpack(tmp_file.read(2 * 4))
            weighted = val * weights[index]
            entry = STRUCT_COL_ENTRY.pack(index, weighted)
            mat_file.write(entry)


def generate_tags_dict(tags_file, max_nb=-1, min_count=0):
    """Generate a dict: tag_name -> row_index.

    If max_nb is positive, we only include the max_nb most popular tags. If
    min_count is positive, we only include the tags that appear at least
    min_count times.
    """
    tags = dict()
    index = 0  # Tag index (i.e. row index).
    f = codecs.open(tags_file, encoding='utf-8')
    for line in f:
        # We assume TAGS_LIST is already sorted by decreasing popularity.
        tag, count = line.split("\t")
        if int(count) < min_count or (max_nb > 0 and index >= max_nb):
            break
        tag = tag.lower()
        if tag not in tags:
            tags[tag] = index
            index += 1
    return tags


def _parse_command():
    parser = argparse.ArgumentParser(description="""Generate a
            tag-track matrix from the MSD tags database.""")
    # Options.
    parser.add_argument('--max-tracks', '-m', type=int, default=-1)
    parser.add_argument('--max-tags', '-M', type=int, default=-1)
    parser.add_argument('--min-tag-count', '-c', type=int, default=0)
    parser.add_argument('--out', '-o', default=MATRIX_PATH)
    parser.add_argument('--tags-out', default=TAGS_PATH)
    parser.add_argument('--weights-out', default=WEIGHTS_PATH)
    # Required arguments.
    parser.add_argument('database')
    parser.add_argument('tags')
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_command()
    print "Generating the [tag_name -> column] mapping.."
    tags = generate_tags_dict(args.tags, max_nb=args.max_tags,
            min_count=args.min_tag_count)
    print "Generating the matrix..."
    create_tree(args.out)
    weights = generate_matrix(tags, args.database, args.out,
            max_nb=args.max_tracks)
    print "Writing the [tag_name -> column] mapping..."
    dump_tags(tags, args.tags_out)
    print "Writing the [column -> global_weight] mapping..."
    dump_weights(weights, args.weights_out)
    print "Done."
