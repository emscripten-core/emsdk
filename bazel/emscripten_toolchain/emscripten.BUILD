package(default_visibility = ['//visibility:public'])

filegroup(
    name = "includes",
    srcs = glob([
        "emscripten/cache/sysroot/include/c++/v1/**",
        "emscripten/cache/sysroot/include/compat/**",
        "emscripten/cache/sysroot/include/**",
        "lib/clang/15.0.0/include/**",
    ]),
)

filegroup(
    name = "compiler_files",
    srcs = [
        "emscripten/emcc.py",
        "bin/clang",
        "bin/clang++",
        ":includes",
    ],
)

filegroup(
    name = "linker_files",
    srcs = [
        "emscripten/emcc.py",
        "bin/llvm-nm",
        "bin/llvm-objcopy",
        "bin/wasm-emscripten-finalize",
        "bin/wasm-ld",
        "bin/wasm-opt",
   ],
)

filegroup(
    name = "ar_files",
    srcs = [
        "emscripten/emar.py",
        "bin/llvm-ar",
   ],
)
