#!/bin/bash

source $(dirname $0)/env.sh

exec $EMSDK_PYTHON $EMSCRIPTEN/emcc.py "$@"
