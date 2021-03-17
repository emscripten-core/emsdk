load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def deps():
    http_archive(
        name = "build_bazel_rules_nodejs",
        sha256 = "0f2de53628e848c1691e5729b515022f5a77369c76a09fbe55611e12731c90e3",
        urls = ["https://github.com/bazelbuild/rules_nodejs/releases/download/2.0.1/rules_nodejs-2.0.1.tar.gz"],
    )

    # emscripten 2.0.15
    http_archive(
        name = "emscripten",
        sha256 = "7ff49fc63adf29970f6e7af1df445d7f554bdbbb2606db1cb5d3567ce69df1db",
        strip_prefix = "install",
        url = "https://storage.googleapis.com/webassembly/emscripten-releases-builds/linux/89202930a98fe7f9ed59b574469a9471b0bda7dd/wasm-binaries.tbz2",
        build_file = "@emsdk//emscripten_toolchain:emscripten.BUILD",
        type = "tar.bz2",
    )
