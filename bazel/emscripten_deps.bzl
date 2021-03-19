load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@build_bazel_rules_nodejs//:index.bzl", "npm_install")
load(":revisions.bzl", "EMSCRIPTEN_TAGS")

def emscripten_deps(version = "2.0.15"):
    revision = EMSCRIPTEN_TAGS[version]

    emscripten_url = "https://storage.googleapis.com/webassembly/emscripten-releases-builds/{}/{}/wasm-binaries.tbz2"

    http_archive(
        name = "emscripten_bin_linux",
        strip_prefix = "install",
        url = emscripten_url.format("linux", revision.hash),
        sha256 = revision.sha_linux,
        build_file = "@emsdk//emscripten_toolchain:emscripten.BUILD",
        type = "tar.bz2",
    )

    npm_install(
        name = "emscripten_npm_linux",
        package_json = "@emscripten_bin_linux//:emscripten/package.json",
        package_lock_json = "@emscripten_bin_linux//:emscripten/package-lock.json",
    )

    native.local_repository(
        name = "emscripten",
        path = "alias",
    )

