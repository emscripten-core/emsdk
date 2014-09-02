#!/bin/bash

pushd `dirname "$_"` > /dev/null
./emsdk construct_env
source ./emsdk_set_env.sh
popd > /dev/null
