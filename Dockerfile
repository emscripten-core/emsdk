# For travis
FROM buildpack-deps:xenial
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN mkdir -p /root/emsdk/
COPY . /root/emsdk/

RUN cd /root/ \
 && echo "int main() {}" > hello_world.cpp \
 && apt-get update \
 && apt-get install -y python python3 cmake build-essential openjdk-9-jre-headless \
 && /root/emsdk/emsdk update-tags \
 && echo "test latest" \
 && /root/emsdk/emsdk install latest \
 && /root/emsdk/emsdk activate latest \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp \
 && emcc hello_world.cpp -s WASM=0 \
 && emcc --clear-cache \
 && echo "test latest-releases-upstream" \
 && python2 /root/emsdk/emsdk install latest-releases-upstream \
 && /root/emsdk/emsdk activate latest-releases-upstream \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp \
 && python -c "import os ; assert open(os.path.expanduser('~/.emscripten')).read().count('LLVM_ROOT') == 1" \
 && python -c "import os ; assert 'upstream' in open(os.path.expanduser('~/.emscripten')).read()" \
 && echo "test latest-releases-fastcomp" \
 && python3 /root/emsdk/emsdk install latest-releases-fastcomp \
 && /root/emsdk/emsdk activate latest-releases-fastcomp \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp \
 && echo "test tot-upstream" \
 && /root/emsdk/emsdk install tot-upstream \
 && /root/emsdk/emsdk activate tot-upstream \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp \
 && echo "test tot-fastcomp" \
 && /root/emsdk/emsdk install tot-fastcomp \
 && /root/emsdk/emsdk activate tot-fastcomp \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp \
 && echo "test show-activated-paths" \
 && /root/emsdk/emsdk show-activated-paths | grep emscripten > a.tmp \
 && /root/emsdk/emsdk show-activated-paths tot-fastcomp | grep emscripten > b.tmp \
 && diff a.tmp b.tmp \
 && echo "test binaryen source build" \
 && /root/emsdk/emsdk install --build=Release binaryen-master-64bit
