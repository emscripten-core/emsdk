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
 && python -c "import os ; assert 'fastcomp' in open(os.path.expanduser('~/.emscripten')).read()" \
 && python -c "import os ; assert 'upstream' not in open(os.path.expanduser('~/.emscripten')).read()" \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp \
 && emcc hello_world.cpp -s WASM=0 \
 && emcc --clear-cache \
 && echo "test latest-releases-upstream" \
 && python2 /root/emsdk/emsdk install latest-upstream \
 && /root/emsdk/emsdk activate latest-upstream \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp \
 && python -c "import os ; assert open(os.path.expanduser('~/.emscripten')).read().count('LLVM_ROOT') == 1" \
 && python -c "import os ; assert 'upstream' in open(os.path.expanduser('~/.emscripten')).read()" \
 && python -c "import os ; assert 'fastcomp' not in open(os.path.expanduser('~/.emscripten')).read()" \
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
 && echo "test specific release (old)" \
 && /root/emsdk/emsdk install 1.38.31 \
 && /root/emsdk/emsdk activate tot-fastcomp \
 && echo "test specific release (new, short name)" \
 && /root/emsdk/emsdk install 1.38.33 \
 && /root/emsdk/emsdk activate tot-fastcomp \
 && python -c "import os ; assert 'fastcomp' in open(os.path.expanduser('~/.emscripten')).read()" \
 && python -c "import os ; assert 'upstream' not in open(os.path.expanduser('~/.emscripten')).read()" \
 && echo "test specific release (new, full name)" \
 && /root/emsdk/emsdk install sdk-1.38.33-upstream-64bit \
 && /root/emsdk/emsdk activate sdk-1.38.33-upstream-64bit \
 && echo "test binaryen source build" \
 && /root/emsdk/emsdk install --build=Release binaryen-master-64bit
