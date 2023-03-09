# Bazel Emscripten toolchain

## Setup Instructions

In `WORKSPACE` file, put:
```
load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
http_archive(
    name = "emsdk",
    sha256 = "d55e3c73fc4f8d1fecb7aabe548de86bdb55080fe6b12ce593d63b8bade54567",
    strip_prefix = "emsdk-3891e7b04bf8cbb3bc62758e9c575ae096a9a518/bazel",
    url = "https://github.com/emscripten-core/emsdk/archive/3891e7b04bf8cbb3bc62758e9c575ae096a9a518.tar.gz",
)

load("@emsdk//:deps.bzl", emsdk_deps = "deps")
emsdk_deps()

load("@emsdk//:emscripten_deps.bzl", emsdk_emscripten_deps = "emscripten_deps")
emsdk_emscripten_deps(emscripten_version = "2.0.31")
```
The SHA1 hash in the above `strip_prefix` and `url` parameters correspond to the git revision of
[emsdk 2.0.31](https://github.com/emscripten-core/emsdk/releases/tag/2.0.31). To get access to
newer versions, you'll need to update those. To make use of older versions, change the
parameter of `emsdk_emscripten_deps()`. Supported versions are listed in `revisions.bzl`


## Building

### Using wasm_cc_binary (preferred)
First, write a new rule wrapping your `cc_binary`.

```
load("@rules_cc//cc:defs.bzl", "cc_binary")
load("@emsdk//emscripten_toolchain:wasm_rules.bzl", "wasm_cc_binary")

cc_binary(
    name = "hello-world",
    srcs = ["hello-world.cc"],
)

wasm_cc_binary(
    name = "hello-world-wasm",
    cc_target = ":hello-world",
)
```

Now you can run `bazel build :hello-world-wasm`. The result of this build will
be the individual files produced by emscripten. Note that some of these files
may be empty. This is because bazel has no concept of optional outputs for
rules.

`wasm_cc_binary` uses transition to use emscripten toolchain on `cc_target`
and all of its dependencies, and does not require amending `.bazelrc`. This
is the preferred way, since it also unpacks the resulting tarball.

See `test_external/` for an example using [embind](https://emscripten.org/docs/porting/connecting_cpp_and_javascript/embind.html).

### Using --config=wasm

Put the following lines into your `.bazelrc`:
```
build:wasm --crosstool_top=@emsdk//emscripten_toolchain:everything
build:wasm --cpu=wasm
build:wasm --host_crosstool_top=@bazel_tools//tools/cpp:toolchain
```

Simply pass `--config=wasm` when building a normal `cc_binary`. The result of
this build will be a tar archive containing any files produced by emscripten.
See the [Bazel documentation](https://docs.bazel.build/versions/main/tutorial/cc-toolchain-config.html)
for more details
