#!/usr/bin/env bash

echo "test the standard workflow (as close as possible to how a user would do it, in the shell)"

set -x
set -e

# Test that arbitrary (non-released) versions can be installed and
# activated.
./emsdk install sdk-upstream-5c776e6a91c0cb8edafca16a652ee1ee48f4f6d2
./emsdk activate sdk-upstream-5c776e6a91c0cb8edafca16a652ee1ee48f4f6d2
source ./emsdk_env.sh
which emcc
emcc -v

./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh --build=Release
# On mac and windows python3 should be in the path and point to the
# bundled version.
which python3
which emcc
emcc -v
