#!/bin/bash
set -e

which asm2wasm
which llvm-ar
which emsdk
node --version
npm --version
python3 --version
pip3 --version
em++ --version
emcc --version
java -version

# cleanup after test
find ${EMSDK} -name "*.pyc" -exec rm {} \;
