#!/bin/bash

export ROOT_DIR=${EXT_BUILD_ROOT:-$(pwd -P)}
export EMSCRIPTEN=$ROOT_DIR/$EM_BIN_PATH/emscripten
export EM_CONFIG=$ROOT_DIR/$EM_CONFIG_PATH

# EMSDK_PYTHON_PATH is set by the Bazel toolchain as a path relative to execroot.
# Make it absolute so that subprocesses (e.g. foreign_rules_cc cmake TryCompile) 
# that run in a different working directory can still find the interpreter when executing emcc.sh.
export EMSDK_PYTHON=$ROOT_DIR/$EMSDK_PYTHON_PATH
