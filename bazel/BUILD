package(default_visibility = ["//visibility:public"])

platform(
    name = "cpu_wasm32",
    constraint_values = [
        "@platforms//cpu:wasm32",
    ],
)

platform(
    name = "cpu_wasm64",
    constraint_values = [
        "@platforms//cpu:wasm64",
    ],
)

filegroup(name = "empty")

alias(
    name = "compiler_files",
    actual = select({
        "@bazel_tools//src/conditions:linux_x86_64": "@emscripten_bin_linux//:compiler_files",
        "@bazel_tools//src/conditions:darwin_x86_64": "@emscripten_bin_mac//:compiler_files",
        "@bazel_tools//src/conditions:darwin_arm64": "@emscripten_bin_mac_arm64//:compiler_files",
        "@bazel_tools//src/conditions:windows": "@emscripten_bin_win//:compiler_files",
        "//conditions:default": ":empty",
    }),
)

alias(
    name = "linker_files",
    actual = select({
        "@bazel_tools//src/conditions:linux_x86_64": "@emscripten_bin_linux//:linker_files",
        "@bazel_tools//src/conditions:darwin_x86_64": "@emscripten_bin_mac//:linker_files",
        "@bazel_tools//src/conditions:darwin_arm64": "@emscripten_bin_mac_arm64//:linker_files",
        "@bazel_tools//src/conditions:windows": "@emscripten_bin_win//:linker_files",
        "//conditions:default": ":empty",
    }),
)

alias(
    name = "ar_files",
    actual = select({
        "@bazel_tools//src/conditions:linux_x86_64": "@emscripten_bin_linux//:ar_files",
        "@bazel_tools//src/conditions:darwin_x86_64": "@emscripten_bin_mac//:ar_files",
        "@bazel_tools//src/conditions:darwin_arm64": "@emscripten_bin_mac_arm64//:ar_files",
        "@bazel_tools//src/conditions:windows": "@emscripten_bin_win//:ar_files",
        "//conditions:default": ":empty",
    }),
)
