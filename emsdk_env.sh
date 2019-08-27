# This script is sourced by the user and uses
# their shell. Try not to use bashisms.

# Do not execute this script without sourcing,
# because it won't have any effect then.
# That is, always run this script with
#
#     . ./emsdk_env.sh
# or
#     source ./emsdk_env.sh
#
# instead of just plainly running with
#
#     ./emsdk_env.sh
#
# which won't have any effect.
SRC="$BASH_SOURCE"
if [ "$SRC" = "" ]; then
  SRC="$0"
fi
CURDIR="$(pwd)"
cd "$(dirname "$SRC")"
unset SRC

tmpfile=`mktemp` || exit 1
./emsdk construct_env $tmpfile
. $tmpfile
rm -f $tmpfile

cd "$CURDIR"
