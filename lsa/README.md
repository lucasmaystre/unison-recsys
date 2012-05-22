# Getting started

First of all, you need to download & unzip the datasets listed in
`../data/README`. Then, merge the datasets:

    # Merge the lastfm_train and lastfm_test datasets.
    mkdir data/lastfm_raw
    cp -rl data/lastfm_test/* data/lastfm_train/* data/lastfm_raw
    rm -r data/lastfm_test data/lastfm_train

To compute the latent space, you need `SVDLIBC`, a singular value decomposition
routine written in C.

    git clone git://github.com/lucasmaystre/svdlibc.git
    cd svdlibc
    make install

You should then be all set. You can test that everything is working as expected
with:

    # Generate a small latent space over a 1000x1000 tag-track matrix.
    make demo
