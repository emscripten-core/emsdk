package(default_visibility = ["//visibility:public"])

config_setting(
    name = "linux",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
    ],
)

config_setting(
    name = "linux_arm64",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:arm64",
    ],
)

config_setting(
    name = "macos",
    constraint_values = [
        "@platforms//os:macos",
        "@platforms//cpu:x86_64",
    ],
)

config_setting(
    name = "macos_arm64",
    constraint_values = [
        "@platforms//os:macos",
        "@platforms//cpu:arm64",
    ],
)

config_setting(
    name = "windows",
    constraint_values = [
        "@platforms//os:windows",
        "@platforms//cpu:x86_64",
    ],
)

filegroup(name = "empty")

alias(
    name = "compiler_files",
    actual = select({
        ":linux": "@emscripten_bin_linux//:compiler_files",
        ":linux_arm64": "@emscripten_bin_linux_arm64//:compiler_files",
        ":macos": "@emscripten_bin_mac//:compiler_files",
        ":macos_arm64": "@emscripten_bin_mac_arm64//:compiler_files",
        ":windows": "@emscripten_bin_win//:compiler_files",
        "//conditions:default": ":empty",
    }),
)

alias(
    name = "linker_files",
    actual = select({
        ":linux": "@emscripten_bin_linux//:linker_files",
        ":linux_arm64": "@emscripten_bin_linux_arm64//:linker_files",
        ":macos": "@emscripten_bin_mac//:linker_files",
        ":macos_arm64": "@emscripten_bin_mac_arm64//:linker_files",
        ":windows": "@emscripten_bin_win//:linker_files",
        "//conditions:default": ":empty",
    }),
)

alias(
    name = "ar_files",
    actual = select({
        ":linux": "@emscripten_bin_linux//:ar_files",
        ":linux_arm64": "@emscripten_bin_linux_arm64//:ar_files",
        ":macos": "@emscripten_bin_mac//:ar_files",
        ":macos_arm64": "@emscripten_bin_mac_arm64//:ar_files",
        ":windows": "@emscripten_bin_win//:ar_files",
        "//conditions:default": ":empty",
    }),
)

platform(
    name = "platform_wasm",
    constraint_values = [
        "@platforms//cpu:wasm32",
        "@platforms//os:emscripten",
    ],
)

platform(
    name = "platform_wasi",
    constraint_values = [
        "@platforms//cpu:wasm32",
        "@platforms//os:wasi",
    ],
)
