load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@build_bazel_rules_nodejs//:index.bzl", "npm_install")
load(":revisions.bzl", "EMSCRIPTEN_TAGS")

def _parse_version(v):
    return [int(u) for u in v.split(".")]

def emscripten_deps(emscripten_version = "latest"):
    version = emscripten_version

    if version == "latest":
        version = reversed(sorted(EMSCRIPTEN_TAGS.keys(), key = _parse_version))[0]

    if version not in EMSCRIPTEN_TAGS.keys():
        error_msg = "Emscripten version {} not found.".format(version)
        error_msg += " Look at @emsdk//:revisions.bzl for the list "
        error_msg += "of currently supported versions."
        fail(error_msg)

    revision = EMSCRIPTEN_TAGS[version]

    emscripten_url = "https://storage.googleapis.com/webassembly/emscripten-releases-builds/{}/{}/wasm-binaries.tbz2"

    # This could potentially backfire for projects with multiple emscripten
    # dependencies that use different emscripten versions
    excludes = native.existing_rules().keys()
    if "emscripten_bin_linux" not in excludes:
        http_archive(
            name = "emscripten_bin_linux",
            strip_prefix = "install",
            url = emscripten_url.format("linux", revision.hash),
            sha256 = revision.sha_linux,
            build_file = "@emsdk//emscripten_toolchain:emscripten.BUILD",
            type = "tar.bz2",
        )

    if "emscripten_bin_mac" not in excludes:
        http_archive(
            name = "emscripten_bin_mac",
            strip_prefix = "install",
            url = emscripten_url.format("mac", revision.hash),
            sha256 = revision.sha_mac,
            build_file = "@emsdk//emscripten_toolchain:emscripten.BUILD",
            type = "tar.bz2",
        )

    if "emscripten_bin_win" not in excludes:
        http_archive(
            name = "emscripten_bin_win",
            strip_prefix = "install",
            url = emscripten_url.format("win", revision.hash),
            sha256 = revision.sha_win,
            build_file = "@emsdk//emscripten_toolchain:emscripten.BUILD",
            type = "tar.bz2",
        )

    if "emscripten_npm_linux" not in excludes:
        npm_install(
            name = "emscripten_npm_linux",
            package_json = "@emscripten_bin_linux//:emscripten/package.json",
            package_lock_json = "@emscripten_bin_linux//:emscripten/package-lock.json",
        )

    if "emscripten_npm_mac" not in excludes:
        npm_install(
            name = "emscripten_npm_mac",
            package_json = "@emscripten_bin_mac//:emscripten/package.json",
            package_lock_json = "@emscripten_bin_mac//:emscripten/package-lock.json",
        )

    if "emscripten_npm_win" not in excludes:
        npm_install(
            name = "emscripten_npm_win",
            package_json = "@emscripten_bin_win//:emscripten/package.json",
            package_lock_json = "@emscripten_bin_win//:emscripten/package-lock.json",
        )
