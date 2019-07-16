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
 && cd /root/emsdk/ \
 && bash test.sh \
 && python test.py
