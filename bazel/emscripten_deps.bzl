load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@build_bazel_rules_nodejs//:index.bzl", "node_repositories", "npm_install")
load(":revisions.bzl", "EMSCRIPTEN_TAGS")

def _parse_version(v):
    return [int(u) for u in v.split(".")]

BUILD_FILE_CONTENT_TEMPLATE = """
package(default_visibility = ['//visibility:public'])

filegroup(
    name = "all",
    srcs = glob(["**"]),
)

filegroup(
    name = "includes",
    srcs = glob([
        "emscripten/cache/sysroot/include/c++/v1/**",
        "emscripten/cache/sysroot/include/compat/**",
        "emscripten/cache/sysroot/include/**",
        "lib/clang/**/include/**",
    ]),
)

filegroup(
    name = "emcc_common",
    srcs = [
        "emscripten/emcc.py",
        "emscripten/emscripten.py",
        "emscripten/emscripten-version.txt",
        "emscripten/cache/sysroot_install.stamp",
        "emscripten/src/settings.js",
        "emscripten/src/settings_internal.js",
    ] + glob(
        include = [
            "emscripten/third_party/**",
            "emscripten/tools/**",
        ],
        exclude = [
            "**/__pycache__/**",
        ],
    ),
)

filegroup(
    name = "compiler_files",
    srcs = [
        "bin/clang{bin_extension}",
        "bin/clang++{bin_extension}",
        ":emcc_common",
        ":includes",
    ],
)

filegroup(
    name = "linker_files",
    srcs = [
        "bin/clang{bin_extension}",
        "bin/llvm-ar{bin_extension}",
        "bin/llvm-dwarfdump{bin_extension}",
        "bin/llvm-nm{bin_extension}",
        "bin/llvm-objcopy{bin_extension}",
        "bin/wasm-ctor-eval{bin_extension}",
        "bin/wasm-emscripten-finalize{bin_extension}",
        "bin/wasm-ld{bin_extension}",
        "bin/wasm-metadce{bin_extension}",
        "bin/wasm-opt{bin_extension}",
        "bin/wasm-split{bin_extension}",
        "bin/wasm2js{bin_extension}",
        ":emcc_common",
    ] + glob(
        include = [
            "emscripten/cache/sysroot/lib/**",
            "emscripten/node_modules/**",
            "emscripten/src/**",
        ],
    ),
)

filegroup(
    name = "ar_files",
    srcs = [
        "bin/llvm-ar{bin_extension}",
        "emscripten/emar.py",
        "emscripten/emscripten-version.txt",
        "emscripten/src/settings.js",
        "emscripten/src/settings_internal.js",
    ] + glob(
        include = [
            "emscripten/tools/**",
        ],
        exclude = [
            "**/__pycache__/**",
        ],
    ),
)
"""

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

    emscripten_url = "https://storage.googleapis.com/webassembly/emscripten-releases-builds/{}/{}/wasm-binaries{}.{}"

    # This could potentially backfire for projects with multiple emscripten
    # dependencies that use different emscripten versions
    excludes = native.existing_rules().keys()
    if "nodejs_toolchains" not in excludes:
        # Node 16 is the first version that supports darwin_arm64
        node_repositories(
            node_version = "16.6.2",
        )

    if "emscripten_bin_linux" not in excludes:
        http_archive(
            name = "emscripten_bin_linux",
            strip_prefix = "install",
            url = emscripten_url.format("linux", revision.hash, "", "tar.xz"),
            sha256 = revision.sha_linux,
            build_file_content = BUILD_FILE_CONTENT_TEMPLATE.format(bin_extension = ""),
            type = "tar.xz",
        )

    if "emscripten_bin_linux_arm64" not in excludes:
        http_archive(
            name = "emscripten_bin_linux_arm64",
            strip_prefix = "install",
            url = emscripten_url.format("linux", revision.hash, "-arm64", "tar.xz"),
            # Not all versions have a linux/arm64 release: https://github.com/emscripten-core/emsdk/issues/547
            sha256 = getattr(revision, "sha_linux_arm64", None),
            build_file_content = BUILD_FILE_CONTENT_TEMPLATE.format(bin_extension = ""),
            type = "tar.xz",
        )

    if "emscripten_bin_mac" not in excludes:
        http_archive(
            name = "emscripten_bin_mac",
            strip_prefix = "install",
            url = emscripten_url.format("mac", revision.hash, "", "tar.xz"),
            sha256 = revision.sha_mac,
            build_file_content = BUILD_FILE_CONTENT_TEMPLATE.format(bin_extension = ""),
            type = "tar.xz",
        )

    if "emscripten_bin_mac_arm64" not in excludes:
        http_archive(
            name = "emscripten_bin_mac_arm64",
            strip_prefix = "install",
            url = emscripten_url.format("mac", revision.hash, "-arm64", "tar.xz"),
            sha256 = revision.sha_mac_arm64,
            build_file_content = BUILD_FILE_CONTENT_TEMPLATE.format(bin_extension = ""),
            type = "tar.xz",
        )

    if "emscripten_bin_win" not in excludes:
        http_archive(
            name = "emscripten_bin_win",
            strip_prefix = "install",
            url = emscripten_url.format("win", revision.hash, "", "zip"),
            sha256 = revision.sha_win,
            build_file_content = BUILD_FILE_CONTENT_TEMPLATE.format(bin_extension = ".exe"),
            type = "zip",
        )

    if "emscripten_npm_linux" not in excludes:
        npm_install(
            name = "emscripten_npm_linux",
            package_json = "@emscripten_bin_linux//:emscripten/package.json",
            package_lock_json = "@emscripten_bin_linux//:emscripten/package-lock.json",
        )

    if "emscripten_npm_linux_arm64" not in excludes:
        npm_install(
            name = "emscripten_npm_linux_arm64",
            package_json = "@emscripten_bin_linux_arm64//:emscripten/package.json",
            package_lock_json = "@emscripten_bin_linux_arm64//:emscripten/package-lock.json",
        )

    if "emscripten_npm_mac" not in excludes:
        npm_install(
            name = "emscripten_npm_mac",
            package_json = "@emscripten_bin_mac//:emscripten/package.json",
            package_lock_json = "@emscripten_bin_mac//:emscripten/package-lock.json",
        )

    if "emscripten_npm_mac_arm64" not in excludes:
        npm_install(
            name = "emscripten_npm_mac",
            package_json = "@emscripten_bin_mac_arm64//:emscripten/package.json",
            package_lock_json = "@emscripten_bin_mac_arm64//:emscripten/package-lock.json",
        )

    if "emscripten_npm_win" not in excludes:
        npm_install(
            name = "emscripten_npm_win",
            package_json = "@emscripten_bin_win//:emscripten/package.json",
            package_lock_json = "@emscripten_bin_win//:emscripten/package-lock.json",
        )
