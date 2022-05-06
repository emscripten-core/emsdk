"""wasm_cc_binary rule for compiling C++ targets to WebAssembly.
"""

def _wasm_transition_impl(settings, attr):
    _ignore = (settings, attr)

    features = list(settings["//command_line_option:features"])
    linkopts = list(settings["//command_line_option:linkopt"])

    if attr.threads == "emscripten":
        # threads enabled
        features.append("use_pthreads")
    elif attr.threads == "off":
        # threads disabled
        features.append("-use_pthreads")

    if attr.exit_runtime == True:
        features.append("exit_runtime")

    if attr.backend == "llvm":
        features.append("llvm_backend")
    elif attr.backend == "emscripten":
        features.append("-llvm_backend")

    if attr.simd:
        features.append("wasm_simd")

    return {
        "//command_line_option:compiler": "emscripten",
        "//command_line_option:crosstool_top": "@emsdk//emscripten_toolchain:everything",
        "//command_line_option:cpu": "wasm",
        "//command_line_option:features": features,
        "//command_line_option:dynamic_mode": "off",
        "//command_line_option:linkopt": linkopts,
        "//command_line_option:platforms": [],
        "//command_line_option:custom_malloc": "@emsdk//emscripten_toolchain:malloc",
    }

_wasm_transition = transition(
    implementation = _wasm_transition_impl,
    inputs = [
        "//command_line_option:features",
        "//command_line_option:linkopt",
    ],
    outputs = [
        "//command_line_option:compiler",
        "//command_line_option:cpu",
        "//command_line_option:crosstool_top",
        "//command_line_option:features",
        "//command_line_option:dynamic_mode",
        "//command_line_option:linkopt",
        "//command_line_option:platforms",
        "//command_line_option:custom_malloc",
    ],
)

_allow_output_extnames = [
    '.js',
    '.wasm',
    '.wasm.map',
    '.worker.js',
    '.js.mem',
    '.data',
    '.fetch.js',
    '.js.symbols',
    '.wasm.debug.wasm',
    '.html',
]

def _wasm_binary_impl(ctx):
    args = ctx.actions.args()
    args.add_joined("--outputs", ctx.outputs.outputs, join_with=",")
    args.add_all("--archive", ctx.files.cc_target)

    for output in ctx.outputs.outputs:
        valid_extname = False
        for allowed_extname in _allow_output_extnames:
            if output.path.endswith(allowed_extname):
                valid_extname = True
                break
        if not valid_extname:
            fail("Invalid output '{}'. Allowed extnames: {}".format(output.basename, ", ".join(_allow_output_extnames)))

    ctx.actions.run(
        inputs = ctx.files.cc_target,
        outputs = ctx.outputs.outputs,
        arguments = [args],
        executable = ctx.executable._wasm_binary_extractor,
    )

    return DefaultInfo(
        # This is needed since rules like web_test usually have a data
        # dependency on this target.
        data_runfiles = ctx.runfiles(transitive_files = depset(ctx.outputs.outputs)),
    )

# Wraps a C++ Blaze target, extracting the appropriate files.
#
# This rule will transition to the emscripten toolchain in order
# to build the the cc_target as a WebAssembly binary.
#
# Args:
#   name: The name of the rule.
#   cc_target: The cc_binary or cc_library to extract files from.
wasm_cc_binary = rule(
    implementation = _wasm_binary_impl,
    attrs = {
        "backend": attr.string(
            default = "_default",
            values = ["_default", "emscripten", "llvm"],
        ),
        "cc_target": attr.label(
            cfg = _wasm_transition,
            mandatory = True,
        ),
        "exit_runtime": attr.bool(
            default = False,
        ),
        "threads": attr.string(
            default = "_default",
            values = ["_default", "emscripten", "off"],
        ),
        "simd": attr.bool(
            default = False,
        ),
        "outputs": attr.output_list(
            allow_empty = False,
            mandatory = True,
        ),
        "_allowlist_function_transition": attr.label(
            default = "@bazel_tools//tools/allowlists/function_transition_allowlist",
        ),
        "_wasm_binary_extractor": attr.label(
            executable = True,
            allow_files = True,
            cfg = "exec",
            default = Label("@emsdk//emscripten_toolchain:wasm_binary"),
        ),
    },
)
