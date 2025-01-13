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
        name = "aspect_rules_js",
        strip_prefix = "rules_js-1.42.0",
        sha256 = "5a00869efaeb308245f8132a671fe86524bdfc4f8bfd1976d26f862b316dc3c9",
        urls = ["https://github.com/aspect-build/rules_js/releases/download/v1.42.0/rules_js-v1.42.0.tar.gz"],
    )

    # Transitive dependencies of aspect_rules_js. We explicitly pull them here instead of calling their
    # provided function to avoid requiring a call to rules_js_dependencies in WORKSPACE.
    maybe(
        http_archive,
        name = "aspect_bazel_lib",
        sha256 = "714cf8ce95a198bab0a6a3adaffea99e929d2f01bf6d4a59a2e6d6af72b4818c",
        strip_prefix = "bazel-lib-2.7.8",
        url = "https://github.com/aspect-build/bazel-lib/releases/download/v2.7.8/bazel-lib-v2.7.8.tar.gz",
    )
    maybe(
        http_archive,
        name = "rules_nodejs",
        strip_prefix = "rules_nodejs-6.3.2",
        sha256 = "158619723f1d8bd535dd6b93521f4e03cf24a5e107126d05685fbd9540ccad10",
        urls = ["https://github.com/bazel-contrib/rules_nodejs/releases/download/v6.3.2/rules_nodejs-v6.3.2.tar.gz"],
    )
    http_archive(
        name = "bazel_features",
        sha256 = "f3082bfcdca73dc77dcd68faace806135a2e08c230b02b1d9fbdbd7db9d9c450",
        strip_prefix = "bazel_features-0.1.0",
        url = "https://github.com/bazel-contrib/bazel_features/releases/download/v0.1.0/bazel_features-v0.1.0.tar.gz",
    )
