#!/usr/bin/env python
"""Generate a database from a list of tags and a feature vectors.

This script writes out a fully populated SQLite database that is basically a
dictionary between tag names and tag representation in the latent space.

It takes as input:
- a marshalled tags dictionary (as output by genmat.py), which links a tag name
  to its column in the matrix
- the *-Ut matrix output by SVDLIBC, in dense binary format. Each row in this
  matrix corresponds to a latent concept, and each column to a tag.
"""

import argparse
import marshal
import sqlite3
import struct

from uutils import (DB_PATH, TAGS_PATH, WEIGHTS_PATH, UT_PATH,
        load_tags, load_weights, create_tree)


TABLE_SCHEMA = """
    CREATE TABLE tags (
      name TEXT,
      vector BLOB,
      weight FLOAT
    );
    CREATE INDEX tags_name_idx ON tags(name);
    """
INSERT_ROW = "INSERT INTO tags (name, vector, weight) VALUES (?, ?, ?)"


def read_vectors(matrix_file, max_dim=-1):
    """Read vectors from a dense binary matrix format.

    This function extracts the latent space representation of each tag from the
    singular value decomposition. The vector is encoded as a string 4 bytes
    floats, one for each latent dimension.
    """
    f = open(matrix_file, 'rb')
    # Get the number of rows and columns.
    nb_rows, = struct.unpack('!l', f.read(4))
    nb_cols, = struct.unpack('!l', f.read(4))
    if max_dim > 0:
        # Only consider the max_dim first dimensions.
        dim = min(nb_rows, max_dim)
    else:
        dim = nb_rows
    # Unfortunately, the vectors are represented as columns. This means we have
    # to process each dimension for all the vectors in parallel.
    vectors = [''] * nb_cols  # Initialization: each vector is an empty string.
    for i in xrange(dim):
        for j in xrange(nb_cols):
            vectors[j] += f.read(4)
    return vectors


def populate_db(tags_dict, weights, vectors, db_file):
    """Create and populate a database with tags, features and weights.
    
    Creates a new SQLite database and fills it with the tags (as strings) and
    their representation in the latent space (feature vectors & associated
    weight).
    """
    conn = init_db(db_file)
    cursor = conn.cursor()
    for tag, index in tags_dict.iteritems():
        values = (tag, buffer(vectors[index]), weights[index])
        cursor.execute(INSERT_ROW, values)
    conn.commit()


def init_db(db_file):
    """Small helper to (re)initalize the database."""
    create_tree(db_file)
    # Trick to truncate the file.
    open(db_file, "w").close()
    conn = sqlite3.connect(db_file);
    # Create the table and index.
    conn.executescript(TABLE_SCHEMA)
    return conn


def _parse_args():
    parser = argparse.ArgumentParser(
            description="Generate a tag features database.")
    parser.add_argument('--matrix', '-m', default=UT_PATH)
    parser.add_argument('--tags', '-t', default=TAGS_PATH)
    parser.add_argument('--weights', '-w', default=WEIGHTS_PATH)
    parser.add_argument('--dim', '-d', type=int, default=-1)
    parser.add_argument('--out', '-o', default=DB_PATH)
    return parser.parse_args()


if __name__ == '__main__':
    args = _parse_args()
    print "Unmarshalling the tags dictionnary..."
    tags_dict = load_tags(args.tags)
    print "Unmarshalling the weights list..."
    weights = load_weights(args.weights)
    print "Read the feature vectors from the matrix..."
    vectors = read_vectors(args.matrix, max_dim=args.dim)
    print "Generate the database..."
    populate_db(tags_dict, weights, vectors, args.out)
    print "Done."
