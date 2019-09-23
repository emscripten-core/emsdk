# Emscripten SDK

[![CircleCI](https://circleci.com/gh/emscripten-core/emsdk/tree/master.svg?style=svg)](https://circleci.com/gh/emscripten-core/emsdk/tree/master)

Emscripten toolchain is distributed as a standalone Emscripten SDK. The SDK
provides all the required tools, such as Clang, Python and Node.js along with an
update mechanism that enables migrating to newer Emscripten versions as they are
released.

You can also set up Emscripten from source, without the pre-built SDK, see
"Installing from Source" below.

## Downloads

To get started with Emscripten development, see the [Emscripten website
documentation](https://emscripten.org/docs/getting_started/downloads.html).

**Old Releases** are available in the **Archived Releases** section below.

## SDK Concepts

The Emscripten SDK is effectively a small package manager for tools that are
used in conjunction with Emscripten. The following glossary highlights the
important concepts to help understanding the internals of the SDK:

* **Tool**: The basic unit of software bundled in the SDK. A Tool has a name and
  a version. For example, 'clang-3.2-32bit' is a Tool that contains the 32-bit
  version of the Clang v3.2 compiler.
* **SDK**: A set of tools. For example, 'sdk-1.5.6-32bit' is an SDK consisting
  of the tools `clang-3.2-32bit`, `node-0.10.17-32bit`, `python-2.7.5.1-32bit`
  and `emscripten-1.5.6`.
* **Active Tool/SDK**: Emscripten stores compiler configuration in a
  user-specific file **~/.emscripten**. This file points to paths for
  Emscripten, Python, Clang and so on. If the file ~/.emscripten is configured
  to point to a Tool in a specific directory, then that tool is denoted as being
  **active**. The Emscripten Command Prompt always gives access to the currently
  active Tools. This mechanism allows switching between different installed SDK
  versions easily.
* **emsdk**: This is the name of the manager script that Emscripten SDK is
  accessed through. Most operations are of the form `emsdk command`. To access
  the emsdk script, launch the Emscripten Command Prompt.

## SDK Maintenance

The following tasks are common with the Emscripten SDK:

##### How do I work the emsdk utility?

Run `emsdk help` or just `emsdk` to get information about all available commands.

##### How do I check the installation status and version of the SDK and tools?

To get a list of all currently installed tools and SDK versions, and all
available tools, run `emsdk list`.
* A line will be printed for each tool/SDK that is available for installation.
* The text `INSTALLED` will be shown for each tool that has already been
  installed.
* If a tool/SDK is currently active, a star * will be shown next to it.
* If a tool/SDK is currently active, but the terminal your are calling emsdk
  from does not have `PATH` and environment set up to utilize that tool, a star
  in parentheses (\*) will be shown next to it. Run `emsdk_env.bat` (Windows) or
  `source ./emsdk_env.sh` (Linux and OS X) to set up the environment for the
  calling terminal.

##### How do I install a tool/SDK version?

Run the command `emsdk install <tool/sdk name>` to download and install a new
tool or an SDK version.

##### How do I remove a tool or an SDK?

Run the command `emsdk uninstall <tool/sdk name>` to delete the given tool or
SDK from the local hard drive completely.

##### How do I check for updates to the Emscripten SDK?

The command `emsdk update` will fetch package information for all new tools and
SDK versions. After that, run `emsdk install <tool/sdk name>` to install a new
version. The command `emsdk update-tags` obtains a list of all new tagged
releases from GitHub without updating Emscripten SDK itself.

##### How do I install an old Emscripten compiler version?

Emsdk contains a history of old compiler versions that you can use to maintain
your migration path. Type `emsdk list --old` to get a list of archived tool and
SDK versions, and `emsdk install <name_of_tool>` to install it.

On Windows, you can directly install an old SDK version by using one of the
archived offline NSIS installers. See the **Archived Releases** section down
below.

##### When working on git branches compiled from source, how do I update to a newer compiler version?

Unlike tags and precompiled versions, a few of the SDK packages are based on
"moving" git branches and compiled from source (sdk-incoming, sdk-master,
emscripten-incoming, emscripten-master, binaryen-master). Because of that, the
compiled versions will eventually go out of date as new commits are introduced
to the development branches. To update an old compiled installation of one of
this branches, simply reissue the "emsdk install" command on that tool/SDK. This
will `git pull` the latest changes to the branch and issue an incremental
recompilation of the target in question. This way you can keep calling `emsdk
install` to keep an Emscripten installation up to date with a given git branch.

Note though that if the previously compiled branch is very old, sometimes CMake
gets confused and is unable to properly rebuild a project. This has happened in
the past e.g. when LLVM migrated to requiring a newer CMake version. In cases of
any odd compilation errors, it is advised to try deleting the intermediate build
directory to clear the build (e.g. "emsdk/clang/fastcomp/build_xxx/") before
reissuing `emsdk install`.

##### How do I change the currently active SDK version?

You can toggle between different tools and SDK versions by running `emsdk
activate <tool/sdk name>`. Activating a tool will set up `~/.emscripten` to
point to that particular tool. On Windows, you can pass the option `--global` to
the `activate` command to register the environment permanently to the system
registry for all users.

##### How do I build multiple projects with different SDK versions in parallel?

By default, Emscripten locates all configuration files in the home directory of
the user. This may be a problem if you need to simultaneously build with
multiple Emscripten compiler versions, since the user home directory can only be
configured to point to one compiler at a time. This can be overcome by
specifying the '--embedded' option as a parameter to 'emsdk activate', which
will signal emsdk to generate the compiler configuration files inside the emsdk
root directory instead of the user home directory. Use this option also when it
is desirable to run emsdk in a fully portable mode that does not touch any files
outside the emsdk directory.

##### How do I track the latest Emscripten development with the SDK?

A common and supported use case of the Emscripten SDK is to enable the workflow
where you directly interact with the github repositories. This allows you to
obtain new features and latest fixes immediately as they are pushed to the
github repository, without having to wait for release to be tagged. You do not
need a github account or a fork of Emscripten to do this. To switch to using the
latest upstream git development branch `incoming`, run the following:

    emsdk install git-1.9.4 # Install git. Skip if the system already has it.
    emsdk install sdk-incoming-64bit # Clone+pull the latest kripken/emscripten/incoming.
    emsdk activate sdk-incoming-64bit # Set the incoming SDK as the currently active one.

If you want to use the upstream stable branch `master`, then replace
`-incoming-` with `-master-` above.

##### How do I use my own Emscripten github fork with the SDK?

It is also possible to use your own fork of the Emscripten repository via the
SDK. This is achieved with standard git machinery, so there if you are already
acquainted with working on multiple remotes in a git clone, these steps should
be familiar to you. This is useful in the case when you want to make your own
modifications to the Emscripten toolchain, but still keep using the SDK
environment and tools. To set up your own fork as the currently active
Emscripten toolchain, first install the `sdk-incoming` SDK like shown in the
previous section, and then run the following commands in the emsdk directory:

    cd emscripten/incoming
    # Add a git remote link to your own repository.
    git remote add myremote https://github.com/mygituseraccount/emscripten.git
    # Obtain the changes in your link.
    git fetch myremote
    # Switch the emscripten-incoming tool to use your fork.
    git checkout -b myincoming --track myremote/incoming

In this way you can utilize the Emscripten SDK tools while using your own git
fork. You can switch back and forth between remotes via the `git checkout`
command as usual.

##### How do I use Emscripten SDK with a custom version of python, java, node.js or some other tool?

The provided Emscripten SDK targets are metapackages that refer to a specific
set of tools that have been tested to work together. For example,
`sdk-1.35.0-64bit` is an alias to the individual packages `clang-e1.35.0-64bit`,
`node-4.1.1-64bit`, `python-2.7.5.3-64bit` and `emscripten-1.35.0`. This means
that if you install this version of the SDK, both python and node.js will be
installed inside emsdk as well. If you want to use your own/system python or
node.js instead, you can opt to install emsdk by specifying the individual set
of packages that you want to use. For example, `emsdk install
clang-e1.35.0-64bit emscripten-1.35.0` will only install the Emscripten
LLVM/Clang compiler and the Emscripten frontend without supplying python and
node.js.

##### My installation fails with "fatal error: ld terminated with signal 9 [Killed]"?

This may happen if the system runs out of memory. If you are attempting to build
one of the packages from source and are running in a virtual OS or have
relatively little RAM and disk space available, then the build might fail. Try
feeding your computer more memory. Another thing to try is to force emsdk
install to build in a singlethreaded mode, which will require less RAM
simultaneously. To do this, pass the `-j1` flag to the `emsdk install` command.

## Uninstalling the Emscripten SDK

If you installed the SDK using an NSIS installer on Windows, launch 'Control
Panel' -> 'Uninstall a program' -> 'Emscripten SDK'.

If you want to remove a Portable SDK, just delete the directory where you put
the Portable SDK into.

## Platform-Specific Notes

##### Mac OS X

* On OS X (and Linux), the git tool will not be installed automatically. Git is
  not a required core component, and is only needed if you want to use one of
  the development branches emscripten-incoming or emscripten-master directly,
  instead of the fixed releases. To install git on OS X, you can

  1. Install XCode, and in XCode, install XCode Command Line Tools. This will
     provide git to the system PATH. For more help on this step, see
     http://stackoverflow.com/questions/9329243/xcode-4-4-command-line-tools
  2. Install git directly from http://git-scm.com/

* Also, on OS X, `java` is not bundled with the Emscripten SDK. After installing
  emscripten via emsdk, typing 'emcc --help' should pop up a OS X dialog "Java
  is not installed. To open java, you need a Java SE 6 runtime. Would you like
  to install one now?" that will automatically download a Java runtime to the
  system.

##### Linux

* On Linux, emsdk does not interact with Linux package managers on the behalf of
  the user, nor does it install any tools to the system. All file changes are
  done inside the `emsdk/` directory.

* Emsdk does not provide `python`, `node` or `java` on Linux. The user is
  expected to install these beforehand with the system package manager.

##### Windows

* On Windows, if you want to build any of the packages from source (instead of
  using the precompiled ones), you will need git, CMake and Visual Studio 2015.
  Git can be installed via emsdk by typing "emsdk install git-1.9.4", CMake can
  be found from http://www.cmake.org/, and Visual Studio can be installed from
  https://www.visualstudio.com.

###### How do I run Emscripten on 32-bit Windows?

Emscripten SDK releases are no longer packaged or maintained for 32-bit Windows.
If you want to run Emscripten on a 32-bit system, you can try manually building
the compiler for 32-bit mode. Follow the steps in the above section "Building an
Emscripten tag or branch from source" to get started.
