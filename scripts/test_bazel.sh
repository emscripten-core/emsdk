#!/usr/bin/env bash

echo "test bazel"

set -x
set -e

cd bazel
bazel build //hello-world:hello-world-wasm
