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

# Install an older version of the SDK that requires EM_CACHE to be
# set in the environment, so that we can test it is later removed
./emsdk install sdk-fastcomp-3b8cff670e9233a6623563add831647e8689a86b
./emsdk activate sdk-fastcomp-3b8cff670e9233a6623563add831647e8689a86b
source ./emsdk_env.sh
which emcc
emcc -v
test -n "$EM_CACHE"

# Install the latest version of the SDK which is the expected precondition
# of test.py.
./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh --build=Release
# Test that EM_CACHE was unset
test -z "$EM_CACHE"

# On mac and windows python3 should be in the path and point to the
# bundled version.
which python3
which emcc
emcc -v
