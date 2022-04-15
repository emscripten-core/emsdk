#!/bin/sh

# 
# This abomination of a script is meant to replace the symlinks
# pointing to the clang-15 binary and set the appropriate flags
# to avoid duplicating the 90MB clang-15 binary inside the nuget
# package.
#
CLANG_NAME=$(basename "$0")
CLANG_CC=$(dirname $0)/clang-15

EXTRA_ARGS=""
case $CLANG_NAME in
    clang)
        ;;
    clang++)
        EXTRA_ARGS="--driver-mode=g++"
        ;;
    *)
        echo "Unknown clang wrapper: $CLANG_NAME"
        exit 1
        ;;
esac

$CLANG_CC $EXTRA_ARGS $@