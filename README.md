To set up the environment, you first need to download & unzip the datasets
listed in data/README. Then, run:

    # Merge the lastfm_train and lastfm_test datasets.
    mkdir data/lastfm_raw
    cp -rl data/lastfm_test/* data/lastfm_train/* data/lastfm_raw
    rm -r data/lastfm_test data/lastfm_train

    # Setup a python virtual environment and install the dependencies.
    virtualenv --distribute venv
    . venv/bin/activate
    pip install -r python-reqs.txt

    # Generate a small latent space over a 1000x1000 tag-track matrix.
    make demo
