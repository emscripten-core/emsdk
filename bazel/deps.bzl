load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
load("@bazel_tools//tools/build_defs/repo:utils.bzl", "maybe")

def deps():
    maybe(
        http_archive,
        name = "platforms",
        urls = [
            "https://mirror.bazel.build/github.com/bazelbuild/platforms/releases/download/0.0.9/platforms-0.0.9.tar.gz",
            "https://github.com/bazelbuild/platforms/releases/download/0.0.9/platforms-0.0.9.tar.gz",
        ],
        sha256 = "5eda539c841265031c2f82d8ae7a3a6490bd62176e0c038fc469eabf91f6149b",
    )
    maybe(
        http_archive,
        name = "bazel_skylib",
        sha256 = "c6966ec828da198c5d9adbaa94c05e3a1c7f21bd012a0b29ba8ddbccb2c93b0d",
        urls = [
            "https://github.com/bazelbuild/bazel-skylib/releases/download/1.1.1/bazel-skylib-1.1.1.tar.gz",
            "https://mirror.bazel.build/github.com/bazelbuild/bazel-skylib/releases/download/1.1.1/bazel-skylib-1.1.1.tar.gz",
        ],
    )
    maybe(
        http_archive,
        name = "rules_nodejs",
        strip_prefix = "rules_nodejs-6.2.0",
        sha256 = "87c6171c5be7b69538d4695d9ded29ae2626c5ed76a9adeedce37b63c73bef67",
        urls = ["https://github.com/bazelbuild/rules_nodejs/releases/download/v6.2.0/rules_nodejs-v6.2.0.tar.gz"],
    )
    maybe(
        http_archive,
        name = "aspect_rules_js",
        strip_prefix = "rules_js-1.42.0",
        sha256 = "5a00869efaeb308245f8132a671fe86524bdfc4f8bfd1976d26f862b316dc3c9",
        urls = ["https://github.com/aspect-build/rules_js/releases/download/v1.42.0/rules_js-v1.42.0.tar.gz"],
    )
