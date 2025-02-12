load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load(":revisions.bzl", "EMSCRIPTEN_TAGS")

def _parse_version(v):
    return [int(u) for u in v.split(".")]

empty_repository = repository_rule(
    implementation = lambda: None,
)

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
        "emscripten/embuilder.py",
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

def _emscripten_deps_impl(ctx):
    version = None

    for mod in ctx.modules:
        for config in mod.tags.config:
            if config.version and version != None:
                fail("More than one emscripten version specified!")
            version = config.version
    if version == None:
        version = "latest"

    if version == "latest":
        version = reversed(sorted(EMSCRIPTEN_TAGS.keys(), key = _parse_version))[0]

    revision = EMSCRIPTEN_TAGS[version]

    emscripten_url = "https://storage.googleapis.com/webassembly/emscripten-releases-builds/{}/{}/wasm-binaries{}.{}"

    http_archive(
        name = "emscripten_bin_linux",
        strip_prefix = "install",
        url = emscripten_url.format("linux", revision.hash, "", "tar.xz"),
        sha256 = revision.sha_linux,
        build_file_content = BUILD_FILE_CONTENT_TEMPLATE.format(bin_extension = ""),
        type = "tar.xz",
    )

    # Not all versions have a linux/arm64 release: https://github.com/emscripten-core/emsdk/issues/547
    if hasattr(revision, "sha_linux_arm64"):
        http_archive(
            name = "emscripten_bin_linux_arm64",
            strip_prefix = "install",
            url = emscripten_url.format("linux", revision.hash, "-arm64", "tar.xz"),
            sha256 = revision.sha_linux_arm64,
            build_file_content = BUILD_FILE_CONTENT_TEMPLATE.format(bin_extension = ""),
            type = "tar.xz",
        )
    else:
        empty_repository(
            name = "emscripten_bin_linux_arm64",
        )

    http_archive(
        name = "emscripten_bin_mac",
        strip_prefix = "install",
        url = emscripten_url.format("mac", revision.hash, "", "tar.xz"),
        sha256 = revision.sha_mac,
        build_file_content = BUILD_FILE_CONTENT_TEMPLATE.format(bin_extension = ""),
        type = "tar.xz",
    )

    http_archive(
        name = "emscripten_bin_mac_arm64",
        strip_prefix = "install",
        url = emscripten_url.format("mac", revision.hash, "-arm64", "tar.xz"),
        sha256 = revision.sha_mac_arm64,
        build_file_content = BUILD_FILE_CONTENT_TEMPLATE.format(bin_extension = ""),
        type = "tar.xz",
    )

    http_archive(
        name = "emscripten_bin_win",
        strip_prefix = "install",
        url = emscripten_url.format("win", revision.hash, "", "zip"),
        sha256 = revision.sha_win,
        build_file_content = BUILD_FILE_CONTENT_TEMPLATE.format(bin_extension = ".exe"),
        type = "zip",
    )

emscripten_deps = module_extension(
    tag_classes = {
        "config": tag_class(
            attrs = {
                "version": attr.string(
                    doc = "Version to use. 'latest' to use latest.",
                    values = ["latest"] + EMSCRIPTEN_TAGS.keys(),
                ),
            },
        ),
    },
    implementation = _emscripten_deps_impl,
)
