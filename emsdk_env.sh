# This script is sourced by the user and uses
# their shell. Try not to use bashisms.

SRC="$BASH_SOURCE"
if [ "$SRC" = "" ]; then
  SRC="$_"
fi
pushd `dirname "$SRC"` > /dev/null
unset SRC

./emsdk construct_env
. ./emsdk_set_env.sh

popd > /dev/null
