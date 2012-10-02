# Unison

Unison is the recommendation system behind **GroupStreamer**, an Android
application that recommends music for groups. You can also checkout the [source
code of the mobile application][1] if you're interested.


## Getting started

You need to define an environment variable, `UNISON_ROOT`, that contains the
path to Unison's root folder. Then, run `bootstrap.sh` which will initialize
some things.

    # Create the one environment variable we need, and run bootstrap.sh.
    export UNISON_ROOT=`pwd`
    ./bootstrap.sh

Unison is mainly written in Python, and uses various libraries. The simplest
thing to do is to create a new virtual environment dedicated to Unison.

    # Setup a python virtual environment and install the dependencies.
    virtualenv --distribute venv
    . venv/bin/activate
    pip install -r python-reqs.txt

    # Unison is currently bundled with two libraries.
    pip install libs/libunison libs/liblfm

Some scripts also require numpy, scipy and matplotlib. If you want to be able to
run everything, you should also install those. Be aware that you'll need a
Fortran compiler.

    # Don't have a fortran compiler? On Mac and with Homebrew, type:
    brew install gfortran

    # Install the Python numerical analysis & computation trifecta.
    pip install numpy
    pip install scipy
    pip install matplotlib

    # You might also have to install scikit-learn to be able to run everything.
    pip install scikit-learn

Unison uses many other tools and software. Hopefully most of it is documented in
the relevant places (checkout the README files in the various subfolders).

**One last (important) thing**: there's a central configuration file that is
expected to live at `$UNISON_ROOT/config.yaml`. Check out the sample
configuration file to see what's expected to be in there.


## Project structure

The project comprises several components, usually organized as subfolders of the
root directory. Here's a brief description of the main parts.

- `data`: contains the raw data from the Million Song Dataset, used to build the
  latent space.
- `lsa`: stands for *Latent Semantic Analysis*. Everything related to building
  the tag-based recommendation system.
- `tagfetch`: the background service that fetches information about tracks from
  Last.fm (tags, cover art, ...).
- `api`: the REST API used by the mobile application to communicate with the
  recommendation system.
- `www`: the main website.
- `scripts`: several utilities that are used to manipulate or visualize the
  data, or perform some maintenance operation.
- `lfm-ratings`: experiments done on user rating data obtained from Last.fm. The
  purpose was to test the effectiveness of the tag-based latent space
  representation of tracks.
- `libs`: contains the Python libraries bundled with Unison.


[1]: https://github.com/lucasmaystre/unison-android
