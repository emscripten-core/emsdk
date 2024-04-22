#!/usr/bin/env bash

echo "test bazel"

set -x
set -e

# Get the latest version number from emscripten-releases-tag.json.
VER=$(ggrep -oP '(?<=latest\": \")([\d\.]+)(?=\")' \
        emscripten-releases-tags.json \
      | sed "s/\./\\\./g")
# Based on the latest version number, get the commit hash for that version.
HASH=$(grep "\"${VER}\"" emscripten-releases-tags.json \
      | grep -v latest \
      | cut -f4 -d\")

FAILMSG="!!! scripts/update_bazel_workspace.py needs to be run !!!"

# Ensure the WORKSPACE file is up to date with the latest version.
grep ${VER} bazel/revisions.bzl || (echo ${FAILMSG} && false)
grep ${HASH} bazel/revisions.bzl || (echo ${FAILMSG} && false)

cd bazel
bazel build //hello-world:hello-world-wasm
bazel build //hello-world:hello-world-wasm-simd

cd test_external
bazel build //long_command_line:long_command_line_wasm
bazel build //:hello-world-wasm
