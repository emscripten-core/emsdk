load("@emsdk//emscripten_toolchain:wasm_rules.bzl", "wasm_cc_binary")

cc_binary(
    name = "hello-world",
    srcs = ["hello-world.cc"],
)

wasm_cc_binary(
    name = "hello-world-wasm",
    cc_target = ":hello-world",
)

cc_binary(
    name = "hello-embind",
    srcs = ["hello-embind.cc"],
    # It's probably a good idea to use select() and config_setting
    # to add different linkopts to BASE_LINKOPTS depending on things
    # like a "opt" or "dbg" compilation mode.
    linkopts = [
        "--bind",       # Enable embind
        "-sMODULARIZE",
    ],
    # This target won't build successfully on its own because of missing emscripten
    # headers etc. Therefore, we hide it from wildcards.
    tags = ["manual"],
)

wasm_cc_binary(
    name = "hello-embind-wasm",
    cc_target = ":hello-embind",
)
