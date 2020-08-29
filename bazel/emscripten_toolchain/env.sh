#!/bin/bash

mkdir -p /tmp/bazel_emscripten/

export ROOT_DIR=`(pwd -P)`
export EMSCRIPTEN=${ROOT_DIR}/external/emscripten/emscripten

export EMCC_WASM_BACKEND=1

export EMCC_SKIP_SANITY_CHECK=1

export EM_CONFIG=${ROOT_DIR}/emscripten_toolchain/emscripten_config
export EM_CACHE=/tmp/bazel_emscripten/emscripten_cache
