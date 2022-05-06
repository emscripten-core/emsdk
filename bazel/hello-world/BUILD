load("@rules_cc//cc:defs.bzl", "cc_binary")
load("//emscripten_toolchain:wasm_rules.bzl", "wasm_cc_binary")

cc_binary(
    name = "hello-world",
    srcs = ["hello-world.cc"],
)

cc_binary(
    name = "hello-world-simd",
    srcs = ["hello-world-simd.cc"],
)

wasm_cc_binary(
    name = "hello-world-wasm",
    cc_target = ":hello-world",
    outputs = [
        "hello-world.wasm",
        "hello-world.js",
    ],
)

wasm_cc_binary(
    name = "hello-world-wasm-simd",
    cc_target = ":hello-world-simd",
    simd = True,
    outputs = [
        "hello-world-simd.wasm",
        "hello-world-simd.js",
    ],
)
