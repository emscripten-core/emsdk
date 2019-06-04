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
 && echo "test the standard workflow (as close as possible to how a user would do it, in the shell)" \
 && /root/emsdk/emsdk install latest \
 && /root/emsdk/emsdk activate latest \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp \
 && emcc hello_world.cpp -s WASM=0 \
 && emcc --clear-cache \
 && echo "run addition tests in python" \
 && cd /root/emsdk/ \
 && python test.py

