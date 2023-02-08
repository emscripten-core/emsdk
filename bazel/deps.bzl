load("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")

def deps():
    excludes = native.existing_rules().keys()

    if "build_bazel_rules_nodejs" not in excludes:
        http_archive(
            name = "build_bazel_rules_nodejs",
            sha256 = "4501158976b9da216295ac65d872b1be51e3eeb805273e68c516d2eb36ae1fbb",
            urls = ["https://github.com/bazelbuild/rules_nodejs/releases/download/4.4.1/rules_nodejs-4.4.1.tar.gz"],
        )
