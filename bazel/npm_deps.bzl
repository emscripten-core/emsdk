load("@build_bazel_rules_nodejs//:index.bzl", "npm_install")

def npm_deps():
    npm_install(
        name = "npm",
        package_json = "@emscripten//:emscripten/package.json",
        package_lock_json = "@emscripten//:emscripten/package-lock.json",
    )
