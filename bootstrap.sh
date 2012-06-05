#!/bin/sh
CURR_DIR=`pwd`

echo "bootstrapping environment...\n"

# Creating the `gen` folder and its symlinks.
mkdir $CURR_DIR/gen
ln -s ../gen $CURR_DIR/lsa/gen
ln -s ../gen $CURR_DIR/scripts/gen
ln -s ../gen $CURR_DIR/itunes/gen

# Checking if UNISON_ROOT has been set properly.
if [ -z $UNISON_ROOT ]; then
    echo "WARNING: environment variable UNISON_ROOT is empty."
    echo "you should run:"
    echo "    export UNISON_ROOT=$CURR_DIR"
fi

echo "\n... done."
