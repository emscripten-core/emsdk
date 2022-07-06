def emsdk_register_toolchains():
    native.register_toolchains("//emscripten_toolchain:cc_wasm32_toolchain")
    native.register_toolchains("//emscripten_toolchain:cc_wasm64_toolchain")