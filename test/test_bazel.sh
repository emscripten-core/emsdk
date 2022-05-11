#!/usr/bin/env bash

echo "test bazel"

set -x
set -e

# Get the latest version number from emscripten-releases-tag.json.
VER=$(grep -oP '(?<=latest\": \")([\d\.]+)(?=\")' \
        emscripten-releases-tags.json \
      | sed --expression "s/\./\\\./g")
# Based on the latest version number, get the commit hash for that version.
HASH=$(grep "\"${VER}\"" emscripten-releases-tags.json \
      | grep -v latest \
      | cut -f4 -d\")

FAILMSG="!!! scripts/update_bazel_toolchain.sh needs to be run !!!"

# Ensure the WORKSPACE file is up to date with the latest version.
grep ${VER} bazel/revisions.bzl || (echo ${FAILMSG} && false)
grep ${HASH} bazel/revisions.bzl || (echo ${FAILMSG} && false)

cd bazel
bazel build //hello-world:hello-world-wasm
bazel build //hello-world:hello-world-wasm-simd

cd test_external
bazel build //:hello-world-wasm
bazel build //:hello-embind-wasm --compilation_mode dbg # debug

# Test use of the closure compiler
bazel build //:hello-embind-wasm --compilation_mode opt # release
# This function should not be minified if the externs file is loaded correctly.
grep "customJSFunctionToTestClosure" bazel-bin/hello-embind-wasm/hello-embind.js