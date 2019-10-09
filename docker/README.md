### About this Dockerfile
... to be added

### Usage

Simple usage of this container to compile a hello-world
```bash
# create helloworld.cpp
cat << EOF > helloworld.cpp
#include <iostream>
int main() {
  std::cout << "Hello World!" << std::endl;
  return 0;
}
EOF
```

```bash
# compile with docker image
docker run \
  --rm \
  -v $(pwd):$(pwd) \
  -u $(id -u):$(id -g) \
  emscripten/emscripten \
  emcc helloworld.cpp -o helloworld.js

# execute on host machine
node helloworld.js
```

Teardown of compilation command:

|part|description|
|---|---|
|`docker run`| A standard command to run a command in a container|
|`--rm`|remove a container after execution (optimization)|
|`-v $(pwd):$(pwd)`|Mounting current folder from the host system into mirrored path on the container<br>TIP: This helps to investigate possible problem as we preserve exactly the same paths like in host. In such case modern editors (like Sublime, Atom, VS Code) let us to CTRL+Click on a problematic file |
|`-u $(id -u):$(id -g)`| Run the container as a non-root user with the same UID and GID as local user. Hence all files produced by this are accessible to non-root users|
|`emscripten/emscripten`|Get the latest tag of this container|
|`emcc helloworld.cpp -o helloworld.js`|Execute `emcc` command with following arguments inside container, effectively compile our source code|



### Building Dockerimage

This image requires to specify following build arguments:

| arg | description |
| --- | --- |
| `EMSCRIPTEN_VERSION` | One of released version of Emscripten. For example `1.38.45`<br/> Can be used with `-upstream` variant like: `1.38.45-upstream`<br /> Minimal supported version is **1.38.40**|

```bash
docker build \
    --build-arg=EMSCRIPTEN_VERSION=1.38.43-upstream \
    --tag test \
    .
```

### Extending

If your project uses packages that this image doesn't provide you might want to:
* Contribute to this repo: Maybe your dependency is either non-intrusive or could be useful for other people
* Create custom image that bases on this image

1. create own Dockerfile that holds:
    ```dockerfile
    # Point at any base image that you find suitable to extend.
    FROM emscripten/emscripten:1.38.25

    # Install required tools that are useful for your project i.e. python2
    RUN apt update && apt install -y python python-pip

    ```
2. build it
    ```shell
    docker build -t extended_emscripten .
    ```

3. test
    ```shell
    docker run --rm extended_emscripten python --version
    # Python 2.7.16
    ```