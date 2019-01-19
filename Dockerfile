# For travis
FROM buildpack-deps:xenial
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN mkdir -p /root/emsdk/
COPY . /root/emsdk/

RUN cd /root/ \
 && echo "int main() {}" > hello_world.cpp \
 && apt-get update \
 && apt-get install -y python cmake build-essential openjdk-9-jre-headless \
 && /root/emsdk/emsdk update-tags \
 && echo "test latest" \
 && /root/emsdk/emsdk install latest \
 && /root/emsdk/emsdk activate latest \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp \
 && echo "test upstream (waterfall)" \
 && /root/emsdk/emsdk install latest-upstream \
 && /root/emsdk/emsdk activate latest-upstream \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp -s WASM_OBJECT_FILES=1 \
 && python -c "import os ; assert open(os.path.expanduser('~/.emscripten')).read().count('LLVM_ROOT') == 1" \
 && python -c "import os ; assert 'upstream' in open(os.path.expanduser('~/.emscripten')).read()" \
 && echo "test fastcomp (waterfall)" \
 && /root/emsdk/emsdk install latest-fastcomp \
 && /root/emsdk/emsdk activate latest-fastcomp \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp \
 && emcc hello_world.cpp -s WASM=0 \
 && echo "test binaryen source build" \
 && /root/emsdk/emsdk install --build=Release binaryen-master-64bit
