BUILD_FILE_CONTENT_TEMPLATE = """
package(default_visibility = ['//visibility:public'])
exports_files(['emscripten_config'])
"""

EMBUILDER_FILE_CONTENT_TEMPLATE = """
CACHE = '{cache}'
EMSCRIPTEN_ROOT = '{emscripten_root}'
BINARYEN_ROOT = '{binaryen_root}'
LLVM_ROOT = '{llvm_root}'

import platform

system = platform.system()
machine = "arm64" if platform.machine() in ('arm64', 'aarch64') else "amd64"
nodejs_binary = "bin/nodejs/node.exe" if(system =="Windows") else "bin/node"
NODE_JS = '{external_root}/nodejs_{{}}_{{}}/{{}}'.format(system.lower(), machine, nodejs_binary)
"""

def get_root_and_script_ext(repository_ctx):
    if repository_ctx.os.name.startswith('linux'):
        if 'amd64' in repository_ctx.os.arch or 'x86_64' in repository_ctx.os.arch:
            return (repository_ctx.path(Label("@emscripten_bin_linux//:BUILD.bazel")).dirname, '')
        elif 'aarch64' in repository_ctx.os.arch:
            return (repository_ctx.path(Label("@emscripten_bin_linux_arm64//:BUILD.bazel")).dirname, '')
        else:
            fail('Unsupported architecture for Linux')
    elif repository_ctx.os.name.startswith('mac'):
        if 'amd64' in repository_ctx.os.arch or 'x86_64' in repository_ctx.os.arch:
            return (repository_ctx.path(Label("@emscripten_bin_mac//:BUILD.bazel")).dirname, '')
        elif 'aarch64' in repository_ctx.os.arch:
            return (repository_ctx.path(Label("@emscripten_bin_mac_arm64//:BUILD.bazel")).dirname, '')
        else:
            fail('Unsupported architecture for MacOS')
    elif repository_ctx.os.name.startswith('windows'):
        fail('Using a secondary cache is not supported on Windows')
        #return (repository_ctx.path(Label("@emscripten_bin_win//:BUILD.bazel")).dirname, '.bat')
    else:
        fail('Unsupported operating system')

def _emscripten_cache_impl(repository_ctx):
    # Read the default emscripten configuration file
    default_config = repository_ctx.read(
        repository_ctx.path(
            Label("@emsdk//emscripten_toolchain:default_config")
        )
    )

    if repository_ctx.attr.libraries or repository_ctx.attr.flags:
        root, script_ext = get_root_and_script_ext(repository_ctx)
        llvm_root = root.get_child("bin")
        emscripten_root = root.get_child("emscripten")
        cache = repository_ctx.path("cache")
        # Ugly hack to get the "external" directory (needed for Windows/Node.js)
        external_root = repository_ctx.path(Label("@nodejs//:BUILD.bazel")).dirname.dirname
        # Create configuration file
        embuilder_config_content = EMBUILDER_FILE_CONTENT_TEMPLATE.format(
            cache=cache,
            emscripten_root=emscripten_root,
            binaryen_root=root,
            llvm_root=llvm_root,
            external_root=external_root,
        )
        repository_ctx.file("embuilder_config", embuilder_config_content)
        embuilder_config_path = repository_ctx.path("embuilder_config")
        embuilder_path = "{}{}".format(emscripten_root.get_child("embuilder"), script_ext)
        # Prepare the command line
        if repository_ctx.attr.libraries:
            libraries = repository_ctx.attr.libraries
        else:
            # If no libraries are requested, build everything
            libraries = ["ALL"]
        flags = ["--em-config", embuilder_config_path] + repository_ctx.attr.flags
        embuilder_args = [embuilder_path] + flags + ["build"] + libraries
        # Run embuilder
        repository_ctx.report_progress("Building secondary cache")
        result = repository_ctx.execute(embuilder_args, quiet=True)
        if result.return_code != 0:
            # Windows fails here because external/nodejs_windows_amd64/bin/nodejs/node.exe
            # does not exist at this point (while the equivalent on Linux and MacOS does)
            fail("Embuilder exited with a non-zero return code")
        # Override Emscripten's cache with the secondary cache
        default_config += "CACHE = '{}'\n".format(cache)

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
