# For travis
FROM buildpack-deps:xenial
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive LANG=C.UTF-8
RUN mkdir -p /root/emscripten/
COPY . /root/emscripten/

RUN cd /root/ \
 && apt-get update \
 && apt-get install -y python cmake build-essential openjdk-9-jre-headless \
 && ./emsdk install latest
 && ./emsdk activate latest
 && source ./emsdk_env.sh --build=Release
 && echo "int main() {}" > hello_world.cpp
 && emcc hello_world.cpp

