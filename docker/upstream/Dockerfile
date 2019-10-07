FROM debian:stretch AS stage_build

# ------------------------------------------------------------------------------

# ATM 1.38.40+ is supported, older will fail with missing /b/s/w/ir/k/install/fastcomp/bin/llc
ARG EMSCRIPTEN_VERSION=1.38.43
ARG EMSCRIPTEN_SDK=${EMSCRIPTEN_VERSION}-upstream
ARG EMSDK_CHANGESET=master

# ------------------------------------------------------------------------------

ENV EMSDK /emsdk_portable
ENV EM_DATA ${EMSDK}/.data
ENV EM_CONFIG ${EMSDK}/.emscripten
ENV EM_CACHE ${EM_DATA}/cache
ENV EM_PORTS ${EM_DATA}/ports

# ------------------------------------------------------------------------------

RUN echo "## Start building" \
    \
&&	echo "## Update and install packages" \
    &&	apt-get -qq -y update \
    # mitigate problem with create symlink to man
    &&  mkdir -p /usr/share/man/man1/ \
    &&  apt-get -qq install -y --no-install-recommends \
            libxml2 \
            wget \
            git-core \
            ca-certificates \
            build-essential \
            file \
            python python-pip \
            python3 python3-pip \
    \
&&  echo "## Done"

RUN  echo "## Get EMSDK" \
    &&  git clone https://github.com/emscripten-core/emsdk.git ${EMSDK} \
    &&  cd ${EMSDK} && git reset --hard ${EMSDK_CHANGESET} \
    \
    &&  ./emsdk.py update-tags \
&&  echo "## Done"

RUN  echo "## Install Emscripten" \
    &&  cd ${EMSDK} \
    && ./emsdk install ${EMSCRIPTEN_SDK} \
    \
&&  echo "## Done"

# This generates configuration that contains all valid paths according to installed SDK
RUN cd ${EMSDK} \
    &&  echo "## Generate standard configuration" \
    \
    &&  ./emsdk activate ${EMSCRIPTEN_SDK} --embedded \
    &&  ./emsdk construct_env > /dev/null \
    &&  cat ${EMSDK}/emsdk_set_env.sh \
    \
    # remove wrongly created entry with EM_CACHE, variable will be picked up from ENV
    &&  sed -i -e "/EM_CACHE/d" ${EMSDK}/emsdk_set_env.sh \
    # add a link to tools like asm2wasm in a system path \
    &&  printf "export PATH=${EMSDK}/upstream/bin:\$PATH\n" >> ${EMSDK}/emsdk_set_env.sh \
    \
&&  echo "## Done"

# Create a structure and make mutable folders accessible for r/w
RUN cd ${EMSDK} \
    &&  echo "## Create .data structure" \
    &&  for mutable_dir in ${EM_DATA} ${EM_PORTS} ${EM_CACHE} ${EMSDK}/zips ${EMSDK}/tmp; do \
            mkdir -p ${mutable_dir}; \
            chmod -R 777 ${mutable_dir}; \
        done \
        \
&&  echo "## Done"


RUN echo "## Create transferable entrypoint" \
    &&  printf '#!/bin/sh\n'                                            >  ${EMSDK}/entrypoint \
    # In case when mapped user id by `docker run -u` is not created inside docker image
    # The `$HOME` variable points to `/` - which prevents any tool to write to, as it requires root access
    # In such case we set `$HOME` to `/tmp` as it should r/w for everyone
    &&  printf 'if [ "$HOME" = "/" ] ; then\n'                          >> ${EMSDK}/entrypoint \
    &&  printf '    export HOME=/tmp\n'                                 >> ${EMSDK}/entrypoint \
    &&  printf 'fi\n'                                                   >> ${EMSDK}/entrypoint \
    &&  printf '\n'                                                     >> ${EMSDK}/entrypoint \
    # In case of running as root, use `umask` to reduce problem of file permission on host
    &&  printf 'if [ "$(id -g)" = "0" ] && [ "$(id -u)" = "0" ] ;\n'    >> ${EMSDK}/entrypoint \
    &&  printf 'then\n'                                                 >> ${EMSDK}/entrypoint \
    &&  printf '    umask 0000\n'                                       >> ${EMSDK}/entrypoint \
    &&  printf 'fi\n'                                                   >> ${EMSDK}/entrypoint \
    # Export this image specific Environment variables
    # Those variables are important to use dedicated folder for all cache and predefined config file
    &&  printf "export EMSDK=${EMSDK}\n"                                >> ${EMSDK}/entrypoint \
    &&  printf "export EM_DATA=${EM_DATA}\n"                            >> ${EMSDK}/entrypoint \
    &&  printf "export EM_CONFIG=${EM_CONFIG}\n"                        >> ${EMSDK}/entrypoint \
    &&  printf "export EM_CACHE=${EM_CACHE}\n"                          >> ${EMSDK}/entrypoint \
    &&  printf "export EM_PORTS=${EM_PORTS}\n"                          >> ${EMSDK}/entrypoint \
    # Activate Emscripten SDK
    &&  printf '. ${EMSDK}/emsdk_set_env.sh > /dev/null\n'              >> ${EMSDK}/entrypoint \
    # Evaluate a command that's coming after `docker run` / `docker exec`
    &&  printf '"$@"\n'                                                 >> ${EMSDK}/entrypoint \
    \
    &&  chmod +x ${EMSDK}/entrypoint \
    \
&&  echo "## Done"


RUN echo "## Create Testing Script" \
    &&  printf '#!/bin/sh\n'                                   >  ${EMSDK}/test.sh \
    &&  printf 'set -e\n'                                      >> ${EMSDK}/test.sh \
    &&  printf 'which asm2wasm\n'                              >> ${EMSDK}/test.sh \
    &&  printf 'which llvm-ar\n'                               >> ${EMSDK}/test.sh \
    &&  printf 'which emsdk\n'                                 >> ${EMSDK}/test.sh \
    &&  printf 'node --version\n'                              >> ${EMSDK}/test.sh \
    &&  printf 'npm --version\n'                               >> ${EMSDK}/test.sh \
    &&  printf 'python --version\n'                            >> ${EMSDK}/test.sh \
    &&  printf 'pip --version\n'                               >> ${EMSDK}/test.sh \
    &&  printf 'python3 --version\n'                           >> ${EMSDK}/test.sh \
    &&  printf 'pip3 --version\n'                              >> ${EMSDK}/test.sh \
    &&  printf 'em++ --version\n'                              >> ${EMSDK}/test.sh \
    &&  printf 'emcc --version\n'                              >> ${EMSDK}/test.sh \
    &&  printf 'find ${EMSDK} -name "*.pyc" -exec rm {} \\;\n' >> ${EMSDK}/test.sh \
    \
    &&  chmod +x ${EMSDK}/test.sh \
    \
&&  echo "## Done"

# Clean up emscripten installation and strip some symbols

RUN apt-get -qq -y update && apt-get -qq install -y --no-install-recommends \
        binutils \
    && . ${EMSDK}/emsdk_set_env.sh \
    # Remove debugging symbols from embedded node (extra 7MB)
    && strip -s `which node` \
    # Tests consume ~80MB disc space
    && rm -fr ${EMSDK}/upstream/emscripten/tests \
    # strip out symbols from clang (extra 50MB!)
    && find ${EMSDK}/upstream/bin -type f -exec strip -s {} + || true \
    && find ${EMSDK}/upstream/fastcomp/bin -type f -exec strip -s {} + || true \
&&  echo "## Done"

# Populate Emscripten SDK cache with libc++, to improve further compilation times.
RUN echo "## Pre-populate cache" \
    &&  . ${EMSDK}/emsdk_set_env.sh \
    \
    &&  mkdir -p /tmp/emscripten_test \
    &&  cd /tmp/emscripten_test \
    \
        &&  printf '#include <iostream>\nint main(){std::cout << "HELLO FROM DOCKER C++"<<std::endl;return 0;}' > test.cpp \
        &&  em++ --std=c++11 test.cpp -o test.js -s WASM=0 &&  node test.js \
        &&  em++ --std=c++11 -g3 test.cpp -o test.js -s WASM=0 &&  node test.js \
        &&  em++ --std=c++11 test.cpp -o test.js -s WASM=1 &&  node test.js \
    \
    &&  cd / \
    &&  rm -fr /tmp/emscripten_test \
    \
    # some files were created, and we need to make sure that those can be accessed by non-root people
    &&  chmod -R 777 ${EM_DATA} \
    \
    # cleanup
    &&  find ${EMSDK} -name "*.pyc" -exec rm {} \; \
    \
    &&  echo "## Done"


# Create symbolic links for critical Emscripten Tools
# This is important for letting people using Emscripten in Dockerfiles without activation
# As each Emscripten release is placed to a different folder (i.e. /emsdk_portable/emscripten/tag-1.38.31)
# The ultimate goal is to simplify a way to use Emscripten SDK without a need to activate it.
RUN echo "## Create symbolic links" \
    &&  . ${EMSDK}/emsdk_set_env.sh \
    \
    &&  mkdir -p ${EMSDK}/llvm ${EMSDK}/emscripten ${EMSDK}/binaryen \
    \
    &&  ln -s $(dirname $(which node))/..       ${EMSDK}/node/current \
    &&  ln -s $(dirname $(which clang))/..      ${EMSDK}/llvm/clang \
    &&  ln -s $(dirname $(which emcc))          ${EMSDK}/emscripten/sdk \
    &&  ln -s $(dirname $(which asm2wasm))      ${EMSDK}/binaryen/bin \
    \
    &&  echo "## Done"


# ------------------------------------------------------------------------------
# -------------------------------- STAGE DEPLOY --------------------------------
# ------------------------------------------------------------------------------

FROM debian:buster-slim AS stage_deploy

COPY --from=stage_build /emsdk_portable /emsdk_portable

# Fallback in case Emscripten isn't activated.
# This will let use tools offered by this image inside other Docker images (sub-stages) or with custom / no entrypoint
ENV EMSDK /emsdk_portable
ENV EMSCRIPTEN=${EMSDK}/emscripten/sdk

ENV EM_DATA ${EMSDK}/.data
ENV EM_CONFIG ${EMSDK}/.emscripten
ENV EM_CACHE ${EM_DATA}/cache
ENV EM_PORTS ${EM_DATA}/ports

# Fallback in case Emscripten isn't activated
# Expose Major tools to system PATH, so that emcc, node, asm2wasm etc can be used without activation
ENV PATH="${EMSDK}:${EMSDK}/upstream/bin:${EMSDK}/emscripten/sdk:${EMSDK}/llvm/clang/bin:${EMSDK}/node/current/bin:${EMSDK}/binaryen/bin:${PATH}"

# Use entrypoint that's coming from emscripten-slim image. It sets all required system paths and variables
ENTRYPOINT ["/emsdk_portable/entrypoint"]


# ------------------------------------------------------------------------------

# Create a 'standard` 1000:1000 user
# Thanks to that this image can be executed as non-root user and created files will not require root access level on host machine
# Please note that this solution even if widely spread (even node Dockerimages use that) is far from perfect as user 1000:1000 might not exist on
# host machine, and in this case running any docker image will cause other random problems (mostly due `$HOME` pointing to `/`)
# This extra user works nicely with entrypoint provided in `/emsdk_portable/entrypoint` as it detects case explained before.
RUN echo "## Create emscripten user (1000:1000)" \
    &&  groupadd --gid 1000 emscripten \
    &&  useradd --uid 1000 --gid emscripten --shell /bin/bash --create-home emscripten \
    \
&&  echo "## Done"

# ------------------------------------------------------------------------------

RUN echo "## Update and install packages" \
&&  mkdir -p /usr/share/man/man1/ \
&&  apt-get -qq -y update && apt-get -qq install -y --no-install-recommends \
        libxml2 \
        ca-certificates \
        python \
        python-pip \
        python3 \
        python3-pip \
        wget \
        curl \
        zip \
        unzip \
        git \
        ssh-client \
        build-essential \
        make \
        ant \
        libidn11 \
        openjdk-11-jre-headless \
    \
    # Standard Cleanup on Debian images
    &&  apt-get -y clean \
    &&  apt-get -y autoclean \
    &&  apt-get -y autoremove \
    &&  rm -rf /var/lib/apt/lists/* \
    &&  rm -rf /var/cache/debconf/*-old \
    &&  rm -rf /usr/share/doc/* \
    &&  rm -rf /usr/share/man/?? \
    &&  rm -rf /usr/share/man/??_* \
&&  echo "## Done"

RUN	echo "## Installing CMake" \
    &&	wget https://cmake.org/files/v3.14/cmake-3.14.3-Linux-x86_64.sh -q \
    &&	mkdir /opt/cmake \
    &&	printf "y\nn\n" | sh cmake-3.14.3-Linux-x86_64.sh --prefix=/opt/cmake > /dev/null \
    &&		rm -fr cmake*.sh /opt/cmake/doc \
    &&		rm -fr /opt/cmake/bin/cmake-gui \
    &&		rm -fr /opt/cmake/bin/ccmake \
    &&		rm -fr /opt/cmake/bin/cpack \
    &&	ln -s /opt/cmake/bin/cmake /usr/local/bin/cmake \
    &&	ln -s /opt/cmake/bin/ctest /usr/local/bin/ctest

# ------------------------------------------------------------------------------

RUN echo "## Internal Testing of image (activated)" \
    &&  . ${EMSDK}/emsdk_set_env.sh \
    &&  ${EMSDK}/test.sh \
    \
&&  echo "## Done"

RUN echo "## Internal Testing of image (not-activated)" \
    &&  ${EMSDK}/test.sh \
    \
&&  echo "## Done"

# ------------------------------------------------------------------------------
# Copy this Dockerimage into image, so that it will be possible to recreate it later
COPY Dockerfile /emsdk_portable/dockerfiles/trzeci/emscripten-upstream/

LABEL maintainer="kontakt@trzeci.eu" \
      org.label-schema.name="emscripten" \
      org.label-schema.description="Regular version of Emscripten compiler what should be suitable to compile majority of C++ projects for Emscripten, ASM.js and WebAssembly." \
      org.label-schema.url="https://trzeci.eu" \
      org.label-schema.vcs-url="https://github.com/trzecieu/emscripten-docker" \
      org.label-schema.docker.dockerfile="/docker/trzeci/emscripten/Dockerfile"

# ------------------------------------------------------------------------------