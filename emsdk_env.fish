# This script is sourced by the user and uses
# their shell. Try not to use bashisms.

# Do not execute this script without sourcing,
# because it won't have any effect then.
# That is, always run this script with
#
#     . ./emsdk_env.fish
# or
#     source ./emsdk_env.fish
#
# instead of just plainly running with
#
#     ./emsdk_env.fish
#
# which won't have any effect.

set -x CURDIR $PWD
set SRC (cd (dirname (status -f)); and pwd) 

cd $SRC
set -e SRC

./emsdk construct_env $argv
. ./emsdk_set_env.sh

cd $CURDIR
