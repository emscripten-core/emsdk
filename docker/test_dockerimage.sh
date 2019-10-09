#!/bin/bash
set -ex

which asm2wasm
which llvm-ar
which emsdk
node --version
npm --version
python3 --version
pip3 --version
python --version
pip --version
em++ --version
emcc --version
java -version
cmake --version

# cleanup after test
find ${EMSDK} -name "*.pyc" -exec rm {} \;
