#!/bin/bash


# Download the tagger package for your system (PC-Linux, Mac OS-X (Intel-CPU), PC-Linux (version for older kernels)).
# Download the tagging scripts into the same directory.
# Download the installation script install-tagger.sh.
# Download the parameter files for the languages you want to process.
# Open a terminal window and run the installation script in the directory where you have downloaded the files:
# "sh install-tagger.sh"

mkdir treetagger && cd treetagger

wget -c http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.tar.gz
wget -c http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz
wget -c http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh
wget -c http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/french-par-linux-3.2-utf8.bin.gz
wget -c http://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/english-par-linux-3.2-utf8.bin.gz


sh install-tagger.sh
