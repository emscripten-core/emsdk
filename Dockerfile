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
 && /root/emsdk/emsdk install latest-upstream \
 && /root/emsdk/emsdk activate latest-upstream \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp -o a.bc \
 && export EMCC_DEBUG=1 \
 && emcc a.bc

