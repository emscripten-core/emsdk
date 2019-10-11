FROM debian:stretch AS stage_build

# ------------------------------------------------------------------------------

# Supports only 1.38.40+, accpets also '-upstream' variants
ARG EMSCRIPTEN_VERSION=1.38.43
ARG EMSDK_CHANGESET=master

# ------------------------------------------------------------------------------

# NOTE: Any change of following variables should be reflected in ./entrypoint file
ENV EMSDK /emsdk
ENV EM_DATA ${EMSDK}/.data
ENV EM_CONFIG ${EMSDK}/.emscripten
ENV EM_CACHE ${EM_DATA}/cache
ENV EM_PORTS ${EM_DATA}/ports

# ------------------------------------------------------------------------------

RUN echo "## Start building" \
    \
&&	echo "## Update and install packages" \
    &&	apt-get -qq -y update \
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
    && ./emsdk install ${EMSCRIPTEN_VERSION} \
    \
&&  echo "## Done"

# This generates configuration that contains all valid paths according to installed SDK
RUN cd ${EMSDK} \
    &&  echo "## Generate standard configuration" \
    \
    &&  ./emsdk activate ${EMSCRIPTEN_VERSION} --embedded \
    &&  ./emsdk construct_env > /dev/null \
    &&  cat ${EMSDK}/emsdk_set_env.sh \
    \
    # remove wrongly created entry with EM_CACHE, variable will be picked up from ENV
    &&  sed -i -e "/EM_CACHE/d" ${EMSDK}/emsdk_set_env.sh \
    # add a link to tools like asm2wasm in a system path
    # asm2wasm (and friends might be places either in ./upstream of ./fastcomp folder, hence detection is needed)
    &&  printf "export PATH=$(dirname $(find . -name asm2wasm -exec readlink -f {} +)):\$PATH\n" >> ${EMSDK}/emsdk_set_env.sh \
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

# Create an entrypoint that activates Emscripten SDK and helps running this image as non-root user
COPY entrypoint ${EMSDK}/


# Create symbolic links for critical Emscripten Tools
# This is important for letting people using Emscripten in Dockerfiles without activation
# As each Emscripten release is placed to a different folder (i.e. /emsdk/emscripten/tag-1.38.31)
RUN echo "## Create symbolic links" \
    &&  . ${EMSDK}/emsdk_set_env.sh \
    \
    &&  mkdir -p ${EMSDK}/llvm ${EMSDK}/emscripten ${EMSDK}/binaryen \
    \
    &&  ln -s $(dirname $(which node))/..       ${EMSDK}/node/current \
    &&  ln -s $(dirname $(which clang))/..      ${EMSDK}/llvm/clang \
    &&  ln -s $(dirname $(which emcc))          ${EMSDK}/emscripten/sdk \
    \
    &&  ln -s $(dirname $(which asm2wasm))      ${EMSDK}/binaryen/bin \
    \
    &&  echo "## Done"

# Clean up emscripten installation and strip some symbols
RUN echo "## Aggresive optimization: Remove debug symbols" \
&&  apt-get -qq -y update && apt-get -qq install -y --no-install-recommends \
        binutils \
    && . ${EMSDK}/emsdk_set_env.sh \
    # Remove debugging symbols from embedded node (extra 7MB)
    && strip -s `which node` \
    # Tests consume ~80MB disc space
    && rm -fr ${EMSDK}/llvm/clang/emscripten/tests \
    # strip out symbols from clang (~extra 50MB disc space)
    && find ${EMSDK}/llvm/clang/bin -type f -exec strip -s {} + || true \
    && find ${EMSDK}/llvm/clang/fastcomp/bin -type f -exec strip -s {} + || true \
&&  echo "## Done"

# Populate Emscripten SDK cache with libc++, to improve further compilation times.
RUN echo "## Pre-populate cache" \
    &&  . ${EMSDK}/emsdk_set_env.sh \
    \
    &&  embuilder.py build SYSTEM \
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

# ------------------------------------------------------------------------------
# -------------------------------- STAGE DEPLOY --------------------------------
# ------------------------------------------------------------------------------

FROM debian:buster-slim AS stage_deploy

COPY --from=stage_build /emsdk /emsdk

# Fallback in case Emscripten isn't activated.
# This will let use tools offered by this image inside other Docker images (sub-stages) or with custom / no entrypoint
ENV EMSDK /emsdk
ENV EMSCRIPTEN=${EMSDK}/emscripten/sdk

ENV EM_DATA ${EMSDK}/.data
ENV EM_CONFIG ${EMSDK}/.emscripten
ENV EM_CACHE ${EM_DATA}/cache
ENV EM_PORTS ${EM_DATA}/ports

# Fallback in case Emscripten isn't activated
# Expose Major tools to system PATH, so that emcc, node, asm2wasm etc can be used without activation
ENV PATH="${EMSDK}:${EMSDK}/emscripten/sdk:${EMSDK}/llvm/clang/bin:${EMSDK}/node/current/bin:${EMSDK}/binaryen/bin:${PATH}"

# Use entrypoint that's coming from emscripten-slim image. It sets all required system paths and variables
ENTRYPOINT ["/emsdk/entrypoint"]


# ------------------------------------------------------------------------------
# Create a 'standard` 1000:1000 user
# Thanks to that this image can be executed as non-root user and created files will not require root access level on host machine
# Please note that this solution even if widely spread (i.e. Node.js uses it) is far from perfect as user 1000:1000 might not exist on
# host machine, and in this case running any docker image will cause other random problems (mostly due `$HOME` pointing to `/`)
# This extra user works nicely with entrypoint provided in `/emsdk/entrypoint` as it detects case explained before.
RUN echo "## Create emscripten user (1000:1000)" \
    &&  groupadd --gid 1000 emscripten \
    &&  useradd --uid 1000 --gid emscripten --shell /bin/bash --create-home emscripten \
    \
&&  echo "## Done"

# ------------------------------------------------------------------------------

RUN echo "## Update and install packages" \
# mitigate problem with create symlink to man for base debian image
    &&  mkdir -p /usr/share/man/man1/ \
    \
    &&  apt-get -qq -y update && apt-get -qq install -y --no-install-recommends \
        libxml2 \
        ca-certificates \
        python \
        python3 \
        python-pip \
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
        cmake \
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

# ------------------------------------------------------------------------------
# Internal test suite of tools that this image provides
COPY test_dockerimage.sh ${EMSDK}/

RUN echo "## Internal Testing of image (activated)" \
    &&  . ${EMSDK}/emsdk_set_env.sh \
    &&  ${EMSDK}/test_dockerimage.sh  \
    \
&&  echo "## Done"

RUN echo "## Internal Testing of image (not-activated)" \
    &&  ${EMSDK}/test_dockerimage.sh  \
    \
&&  echo "## Done"

# ------------------------------------------------------------------------------
# Copy this Dockerimage into image, so that it will be possible to recreate it later
COPY Dockerfile /emsdk/dockerfiles/emscripten-core/emsdk/

LABEL maintainer="kontakt@trzeci.eu" \
      org.label-schema.name="emscripten" \
      org.label-schema.description="The official container with Emscripten SDK" \
      org.label-schema.url="https://emscripten.org" \
      org.label-schema.vcs-url="https://github.com/emscripten-core/emsdk" \
      org.label-schema.docker.dockerfile="/docker/Dockerfile"

# ------------------------------------------------------------------------------
