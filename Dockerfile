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
 && /root/emsdk/emsdk install latest \
 && /root/emsdk/emsdk activate latest \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && emcc hello_world.cpp \
 && /root/emsdk/emsdk update-tags \
 && /root/emsdk/emsdk install latest-upstream \
 && echo "activate!" \
 && /root/emsdk/emsdk activate latest-upstream \
 && echo "activated" \
 && source /root/emsdk/emsdk_env.sh --build=Release \
 && find -name "emcc.py" \
 && emcc hello_world.cpp \

