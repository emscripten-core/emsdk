FROM debian:buster AS stage_build

ARG EMSCRIPTEN_VERSION=1.39.18
ENV EMSDK /emsdk

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
            python3 python3-pip \
&&  echo "## Done"

RUN  echo "## Get EMSDK" \
    &&  git clone https://github.com/emscripten-core/emsdk.git ${EMSDK} \
&&  echo "## Done"

RUN  echo "## Install Emscripten" \
    &&  cd ${EMSDK} \
    &&  ./emsdk install ${EMSCRIPTEN_VERSION} \
&&  echo "## Done"

# This generates configuration that contains all valid paths according to installed SDK
RUN cd ${EMSDK} \
    &&  echo "## Generate standard configuration" \
    &&  ./emsdk activate ${EMSCRIPTEN_VERSION} \
    &&  ./emsdk construct_env \
    &&  cat ${EMSDK}/emsdk_set_env.sh \
    &&  chmod -R 777 ${EMSDK}/upstream/emscripten/cache \
&&  echo "## Done"

# Clean up emscripten installation and strip some symbols
RUN echo "## Aggresive optimization: Remove debug symbols" \
&&  apt-get -qq -y update && apt-get -qq install -y --no-install-recommends \
        binutils \
    && . ${EMSDK}/emsdk_set_env.sh \
    # Remove debugging symbols from embedded node (extra 7MB)
    && strip -s `which node` \
    # Tests consume ~80MB disc space
    && rm -fr ${EMSDK}/upstream/emscripten/tests \
    # Fastcomp is not supported
    && rm -fr ${EMSDK}/upstream/fastcomp \
    # strip out symbols from clang (~extra 50MB disc space)
    && find ${EMSDK}/upstream/bin -type f -exec strip -s {} + || true \
&&  echo "## Done"

# Generate sanity
# TODO(sbc): We should be able to use just emcc -v here but it doesn't
# currently create the sanity file.
RUN echo "## Generate sanity" \
   &&  . ${EMSDK}/emsdk_set_env.sh \
   &&  echo "int main() { return 0; }" > hello.c \
   &&  emcc -c hello.c \
   &&  cat ${EMSDK}/.emscripten_sanity \
&&  echo "## Done"

# ------------------------------------------------------------------------------
# -------------------------------- STAGE DEPLOY --------------------------------
# ------------------------------------------------------------------------------

FROM debian:buster-slim AS stage_deploy

COPY --from=stage_build /emsdk /emsdk

# Fallback in case Emscripten isn't activated.
# This will let use tools offered by this image inside other Docker images
# (sub-stages) or with custom / no entrypoint
ENV EMSDK_NODE=/emsdk/node/12.18.1_64bit/bin/node
ENV EMSDK=/emsdk
ENV EM_CONFIG=/emsdk/.emscripten
ENV PATH="${EMSDK}:${EMSDK}/upstream/emscripten:${EMSDK}/upstream/bin:emsdk/node/12.18.1_64bit/bin:${PATH}"

# ------------------------------------------------------------------------------
# Create a 'standard` 1000:1000 user
# Thanks to that this image can be executed as non-root user and created files
# will not require root access level on host machine Please note that this
# solution even if widely spread (i.e. Node.js uses it) is far from perfect as
# user 1000:1000 might not exist on host machine, and in this case running any
# docker image will cause other random problems (mostly due `$HOME` pointing to
# `/`)
RUN echo "## Create emscripten user (1000:1000)" \
    &&  groupadd --gid 1000 emscripten \
    &&  useradd --uid 1000 --gid emscripten --shell /bin/bash --create-home emscripten \
    &&  echo "umask 0000" >> /etc/bash.bashrc \
    &&  echo ". /emsdk/emsdk_set_env.sh" >> /etc/bash.bashrc \
&&  echo "## Done"

# ------------------------------------------------------------------------------

RUN echo "## Update and install packages" \
# mitigate problem with create symlink to man for base debian image
    &&  mkdir -p /usr/share/man/man1/ \
    \
    &&  apt-get -qq -y update && apt-get -qq install -y --no-install-recommends \
        libxml2 \
        ca-certificates \
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
COPY test_dockerimage.sh /emsdk/

RUN echo "## Internal Testing of image" \
    &&  /emsdk/test_dockerimage.sh  \
&&  echo "## Done"

# ------------------------------------------------------------------------------
# Copy this Dockerimage into image, so that it will be possible to recreate it later
COPY Dockerfile /emsdk/dockerfiles/emscripten-core/emsdk/

# ------------------------------------------------------------------------------
# Use commonly used /src as working directory
WORKDIR /src

LABEL maintainer="kontakt@trzeci.eu" \
      org.label-schema.name="emscripten" \
      org.label-schema.description="The official container with Emscripten SDK" \
      org.label-schema.url="https://emscripten.org" \
      org.label-schema.vcs-url="https://github.com/emscripten-core/emsdk" \
      org.label-schema.docker.dockerfile="/docker/Dockerfile"

# ------------------------------------------------------------------------------
