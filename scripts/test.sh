#!/usr/bin/env bash

echo "test the standard workflow (as close as possible to how a user would do it, in the shell)"

set -x
set -e

./emsdk install latest
./emsdk activate latest
source ./emsdk_env.sh --build=Release
emcc -v
