#In your Fish configuration, add this line:
#alias emsdk_setup ". /path/to/emsdk/emsdk_env.fish"
#Now, when you want to use the SDK, run this alias first to set up
#your environment.

set -l script (status -f)
set -l dir (dirname $script)

pushd $dir > /dev/null

./emsdk construct_env
. ./emsdk_set_env.sh

set -e -l script
set -e -l dir

popd > /dev/null
