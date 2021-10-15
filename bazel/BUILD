package(default_visibility = ["//visibility:public"])

config_setting(
    name = "linux",
    constraint_values = [
        "@platforms//os:linux",
        "@platforms//cpu:x86_64",
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
    name = "windows",
    constraint_values = [
        "@platforms//os:windows",
        "@platforms//cpu:x86_64",
    ],
)

alias(
    name = "binaries",
    actual = select({
        ":linux": "@emscripten_bin_linux//:all",
        ":macos": "@emscripten_bin_mac//:all",
        ":windows": "@emscripten_bin_win//:all",
    }),
)

alias(
    name = "node_modules",
    actual = select({
        ":linux": "@emscripten_npm_linux//:node_modules",
        ":macos": "@emscripten_npm_mac//:node_modules",
        ":windows": "@emscripten_npm_win//:node_modules",
    }),
)
