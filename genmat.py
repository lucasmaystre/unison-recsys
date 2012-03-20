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
"""

import marshal
import optparse
import os
import sqlite3
import struct


# Files.
TAGS_DATABASE = 'data/lastfm_tags.db'
TAGS_FREQUENCY = 'data/lastfm_unique_tags.txt'
TAGS_DICT_SERIALIZED = './tags_dict.dat'
MATRIX_FILE = './tag_track.mat'

# SQL queries.
QUERY_ALL_TRACKS = "SELECT tid FROM tids"
QUERY_TAGS_FOR_TRACK = ("SELECT tags.tag FROM tags, tid_tag, tids "
        + "WHERE tags.ROWID = tid_tag.tag "
        + "AND tid_tag.tid = tids.ROWID "
        + "AND tids.tid = ?")

# Compiled Struct objects to avoid reparsing the format everytime.
STRUCT_COL_HEADER = struct.Struct("!l")
STRUCT_COL_ENTRY = struct.Struct("!lf")


def generate_matrix(tags_dict, max_nb=-1):
    """Write out a tag-track matrix in the sparse binary matrix format.

    Fetches the tracks and tags from the SQLite database. Restricts the tags to
    those in 'tags_dict', and optionally stops after 'max_nb' tracks.
    """
    mat_file = open(MATRIX_FILE, 'wb')
    update_header(mat_file)
    # Initialize the matrix header values.
    nb_rows = len(tags_dict)  # Number of tags.
    nb_cols = 0  # Will be equal to the number of tracks.
    nb_non_zero = 0  # Total number of nonzero values.

    # Set up the connection to the database, and create two cursors.
    conn = sqlite3.connect(TAGS_DATABASE)
    tracks_cursor = conn.cursor()
    tags_cursor = conn.cursor()
    # Iterate over all tracks.
    tracks_cursor.execute(QUERY_ALL_TRACKS)
    for track in tracks_cursor:
        column = list()
        # Iterate over the associated tags.
        tags_cursor.execute(QUERY_TAGS_FOR_TRACK, (track[0],))
        for tag in tags_cursor:
            if tag[0] in tags_dict:
                entry = (tags_dict[tag[0]], 1)
                column.append(entry)
        if len(column) == 0:
            # The track results in an all-zero column. Skip it.
            continue
        # Update track count and non-zero value count.
        nb_cols += 1
        nb_non_zero += len(column)
        append_column(mat_file, column)
        if max_nb > 0 and nb_cols >= max_nb:
            break  # We're done, we have enough tracks.
    # We're done! We just need to update the header with the correct values.
    update_header(mat_file, rows=nb_rows, cols=nb_cols, total=nb_non_zero)
    mat_file.close()


def update_header(mat_file, rows=0, cols=0, total=0):
    """Update the header for a matrix in sparse binary format.

    The file 'mat_file' has to be opened with the flags r+b or wb to allow
    writing anywhere in the file.
    """
    # Exclamation point (!) means network byte order (big endian).
    data = struct.pack('!lll', rows, cols, total)
    mat_file.seek(0)
    mat_file.write(data)


def append_column(mat_file, column):
    """Append a new column to a sparse binary matrix."""
    mat_file.seek(0, os.SEEK_END)  # Append to the file.
    mat_file.write(STRUCT_COL_HEADER.pack(len(column)))
    for entry in column:
        mat_file.write(STRUCT_COL_ENTRY.pack(*entry))


def generate_tags_dict(max_nb=-1, min_count=0):
    """Generate a dict: tag_name -> row_index.

    If max_nb is positive, we only include the max_nb most popular tags. If
    min_count is positive, we only include the tags that appear at least
    min_count times.
    """
    tags = dict()
    index = 0  # Tag index (i.e. row index).
    for line in open(TAGS_FREQUENCY):
        # We assume TAGS_LIST is already sorted by decreasing popularity.
        tag, count = line.split("\t")
        if int(count) < min_count or (max_nb > 0 and index >= max_nb):
            break
        tags[tag] = index
        index += 1
    return tags


def dump_tags_dict(tags_dict):
    """Write a marshalled tags dict to disk."""
    f = open(TAGS_DICT_SERIALIZED, 'wb')
    marshal.dump(tags_dict, f)


def load_tags_dict():
    """Read a marshalled tags dict from disk."""
    f = open(TAGS_DICT_SERIALIZED, 'rb')
    return marshal.load(f)


def _parse_command():
    parser = optparse.OptionParser()
    parser.add_option('--max-tracks', action='store', type='int',
            dest='max_tracks', default=-1)
    parser.add_option('--max-tags', action='store', type='int',
            dest='max_tags', default=-1)
    parser.add_option('--min-tag-count', action='store', type='int',
            dest='min_tag_count', default=0)
    return parser.parse_args()


if __name__ == '__main__':
    # TODO make a nicer command line utility (where to save the .mat file? do we
    # want to save / load a marshalled tags_dict?)
    options, args = _parse_command()
    tags = generate_tags_dict(
            max_nb=options.max_tags, min_count=options.min_tag_count)
    generate_matrix(tags, max_nb=options.max_tracks)
