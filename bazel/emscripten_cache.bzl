BUILD_FILE_CONTENT_TEMPLATE = """
package(default_visibility = ['//visibility:public'])
exports_files(['emscripten_config'])
"""

def _emscripten_cache_impl(repository_ctx):
    # Read the default emscripten configuration file
    default_config = repository_ctx.read(
        repository_ctx.path(
            Label("@emsdk//emscripten_toolchain:default_config")
        )
    )

    # TODO I need a cross platform way to get embuilder and bin/node
    if repository_ctx.attr.libraries or repository_ctx.attr.flags:
        # Get paths to tools (toolchain is not yet setup, so we cannot use emscripten_config)
        embuilder_path = repository_ctx.path(Label("@emscripten_bin_linux//:emscripten/embuilder.py"))
        binaryen_root = embuilder_path.dirname.dirname
        llvm_root = binaryen_root.get_child("bin")
        nodejs = repository_ctx.path(Label("@nodejs//:node_files")).dirname.get_child('bin/node')
        # Create configuration file
        embuilder_config_content  = "LLVM_ROOT = '{}'\n".format(llvm_root)
        embuilder_config_content += "NODE_JS = '{}'\n".format(nodejs)
        embuilder_config_content += "BINARYEN_ROOT = '{}'\n".format(binaryen_root)
        embuilder_config_content += "CACHE = 'cache'\n"
        repository_ctx.file('embuilder_config', embuilder_config_content)
        embuilder_config_path = repository_ctx.path('embuilder_config')
        # Prepare the command line
        if repository_ctx.attr.libraries:
            libraries = repository_ctx.attr.libraries
        else:
            # if no libraries are requested, build everything
            libraries = ["ALL"]
        flags = ["--em-config", embuilder_config_path] + repository_ctx.attr.flags
        embuilder_args = [embuilder_path] + flags + ["build"] + libraries
        # Run embuilder
        repository_ctx.report_progress("Building secondary cache")
        repository_ctx.execute(embuilder_args, quiet=False)
        # Override Emscripten's cache with the secondary cache
        default_config += "CACHE = '{}'\n".format(repository_ctx.path('cache'))
    # Create the configuration file for the toolchain and export
    repository_ctx.file('emscripten_config', default_config)
    repository_ctx.file('BUILD.bazel', BUILD_FILE_CONTENT_TEMPLATE)

_emscripten_cache = repository_rule(
    implementation = _emscripten_cache_impl,
    attrs = {
        "flags": attr.string_list(),
        "libraries": attr.string_list(),
    },
    local = True
)

def emscripten_cache(flags = [], libraries = []):
    _emscripten_cache(
        name = "emscripten_cache",
        flags = flags,
        libraries = libraries,
    )
