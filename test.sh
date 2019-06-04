echo "test the standard workflow (as close as possible to how a user would do it, in the shell)"
/root/emsdk/emsdk install latest
/root/emsdk/emsdk activate latest
source /root/emsdk/emsdk_env.sh --build=Release
emcc hello_world.cpp
emcc hello_world.cpp -s WASM=0
emcc --clear-cache

