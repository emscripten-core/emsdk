#!/bin/bash

pushd `dirname "$BASH_SOURCE"` > /dev/null
./emsdk construct_env
source ./emsdk_set_env.sh
popd > /dev/null
