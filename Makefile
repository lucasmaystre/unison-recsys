default: demo

matrix:
	echo "Generate the tag-track matrix..."
	time ./genmat.py data/lastfm_tags.db data/lastfm_unique_tags.txt

svd: matrix
	echo "Perform the d-dimensional SVD approximation..."
	time svd -r sb -w db -o gen/result -d 70 gen/tag-track.mat

lspace: matrix svd
	echo "Generate the database containing the latent space description..."
	time ./gendb.py

demo:
	./genmat.py -m 1000 -M 1000 data/lastfm_tags.db data/lastfm_unique_tags.txt
	svd -r sb -w db -o gen/result -d 15 gen/tag-track.mat
	./gendb.py

clean:
	echo "Cleaning the generated files..."
	rm -rf gen/

.PHONY: default lspace svd matrix demo clean
