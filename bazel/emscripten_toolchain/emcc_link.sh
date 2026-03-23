#!/bin/bash

source $(dirname $0)/env.sh

exec $EMSDK_PYTHON $(dirname $0)/link_wrapper.py "$@"
