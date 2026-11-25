#!/bin/bash

export ROOT_DIR=${EXT_BUILD_ROOT:-$(pwd -P)}
export EMSCRIPTEN=$ROOT_DIR/$EM_BIN_PATH/emscripten
export EM_CONFIG=$ROOT_DIR/$EM_CONFIG_PATH
export EMSDK_PYTHON=$ROOT_DIR/$BAZEL_PYTHON_RELPATH

# Keep Python from resolving the sandbox symlink of the entry script (emcc.py,
# em++.py, emar.py) when computing sys.path[0]. Otherwise emscripten's `tools`
# package is imported from the real external repository directory, its root
# (tools/utils.py:__rootpath__) points outside the sandbox and undeclared
# toolchain inputs go unnoticed in local sandboxed builds. Requires Python 3.11+.
export PYTHONSAFEPATH=1
export PYTHONPATH=$EMSCRIPTEN
