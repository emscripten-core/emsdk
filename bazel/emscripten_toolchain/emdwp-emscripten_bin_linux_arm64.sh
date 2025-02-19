#!/bin/bash
#
#  This script differs in form from emcc.{py,bat}/…, because bazel are limited/bugged in the way of executing dwp tool.
#  Bazel dwp action configuration does not pass environment variables, so we cannot use them in this script.
#  For more info, see PR discussion and bazel issue:
#  - https://github.com/emscripten-core/emsdk/pull/1531#discussion_r1962090650
#  - https://github.com/bazelbuild/bazel/issues/25336
#

exec external/emscripten_bin_linux_arm64/bin/llvm-dwp "$@"
