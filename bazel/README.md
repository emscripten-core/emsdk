# Bazel Emscripten toolchain

## Setup Instructions

In `WORKSPACE` file, put:
```starlark
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

load("@emsdk//:toolchains.bzl", "register_emscripten_toolchains")
register_emscripten_toolchains()
```
The SHA1 hash in the above `strip_prefix` and `url` parameters correspond to the git revision of
[emsdk 2.0.31](https://github.com/emscripten-core/emsdk/releases/tag/2.0.31). To get access to
newer versions, you'll need to update those. To make use of older versions, change the
parameter of `emsdk_emscripten_deps()`. Supported versions are listed in `revisions.bzl`


## Building

Put the following line into your `.bazelrc`:

```
build --incompatible_enable_cc_toolchain_resolution
```

Then write a new rule wrapping your `cc_binary`.

```starlark
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
