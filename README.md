# Emscripten SDK

Emscripten toolchain is distributed as a standalone Emscripten SDK. The SDK provides all the required tools, such as Clang, Python and Node.js along with an update mechanism that enables migrating to newer Emscripten versions as they are released.

You can also set up Emscripten from source, without the pre-built SDK, see "Installing from Source" below.

## Downloads

To get started with Emscripten development, see the [Emscripten website documentation](https://kripken.github.io/emscripten-site/docs/getting_started/downloads.html).

**Old Releases** are available in the **Archived Releases** section below.

## Installation Instructions

The initial setup process is as follows:

1. Download and unzip the portable SDK package to a directory of your choice. This directory will contain the Emscripten SDK.
2. Open a command prompt to the directory of the SDK.
3. Run `emsdk update`. This will fetch the latest registry of available tools.
4. Run `emsdk install latest`. This will download and install the latest set of precompiled SDK tools.
5. Run `emsdk activate latest`. This will set up **~/.emscripten** to point to the SDK.
6. Depending on your OS:
 - OS X and Linux: Run `source ./emsdk_env.sh`. This will add PATH and other required environment variables to the currently executing terminal prompt. If you want to permanently add these environment variables to each terminal instance on your system, add a call to this command to `.bash_profile` or another initialization script for your terminal.
 - Windows: Call `emsdk_env.bat` to add PATH and other environment variables to the current command prompt. If you want to persist these environment variables to all command prompts, run `emsdk activate --global latest` to have Emsdk edit the Windows registry to add these variables.

Whenever you change the location of the Portable SDK (e.g. take it to another computer), re-run steps 5 and 6. If you choose not to permanently add the environment variables to all terminal prompts, rerun step 6 whenever opening a new terminal window.

Note: On Linux and OS X, type `./emsdk` instead of `emsdk` above.

### Building an Emscripten tag or branch from source

In addition to providing precompiled compiler versions, Emscripten SDK automates driving builds of the Emscripten toolchain from source. These builds obtain the source code directly from GitHub, and can either target a specific tagged release, or one of the two main Emscripten development branches, `incoming` and `master`. Building tagged releases from source is useful to build a version of Emscripten that there is no provided precompiled build available. Building one of the development branches is useful when you want to get the very latest version from source, e.g. to verify a brand new bugfix, or to participate to Emscripten development.

To build one of the tagged releases from source, run the following steps:

1. Open a command prompt to the directory of the SDK.
2. Run `emsdk update-tags`. This will ping GitHub to obtain the latest list of known tags in the different repositories.
3. Run `emsdk list` to check out the list of available tags. Look for the section "The following SDKs can be compiled from source".
4. Proceed through the steps 4, 5 and 6 above, except substitute `latest` with the SDK version of your choice, for example `emsdk install sdk-tag-1.37.9-64bit` followed by `emsdk activate sdk-tag-1.37.9-64bit`.

To build one of the Github branches, `emsdk install` one of the targets `sdk-incoming-64bit` or `sdk-master-64bit`.

Building Emscripten involves building LLVM with Clang from source. LLVM build configuration allows specifying a number of extra configuration fields, see here: http://llvm.org/docs/CMake.html. To build the SDK with a specific set of custom CMake parameters, run the emsdk build script with the environment variable `LLVM_CMAKE_ARGS="param1=value1,param2=value2,..."`. For example, to use the gold linker to link the final Clang executable and to enable assertions, run the installation with the command `LLVM_CMAKE_ARGS="-DLLVM_USE_LINKER=gold,-DLLVM_ENABLE_ASSERTIONS=ON" ./emsdk install sdk-incoming-64bit`.

### Installing emsdk directly from GitHub

If you want to bootstrap to the development version of emsdk instead of the stable releases, you can do so by installing emsdk directly from github. Functionally this behaves identical to the Portable SDK. As a prerequisite on Windows, you must first manually download and install [Python](https://www.python.org) to bootstrap, and after that, run:

    git clone https://github.com/juj/emsdk.git
    cd emsdk
    ./emsdk update-tags
    ./emsdk install <sdk-of-your-choice>
    ./emsdk activate <sdk-of-your-choice>
    source ./emsdk_env.sh (Windows: emsdk_env.bat)

The only difference in this setup is that you will then use `git pull` instead of `./emsdk update` to update to a newer version of Emscripten SDK.

## Getting Started with Emscripten

The tools in the Emscripten toolchain can be accessed in various ways. Which one you use depends on your preference.

##### Command line usage

The Emscripten compiler is available on the command line by invoking `emcc` or `em++`. They are located in the folder `emsdk/emscripten/<version>/` in the SDK.

The root directory of the Emscripten SDK contains scripts `emsdk_env.bat` (Windows) and `emsdk_env.sh` (Linux, OS X) which set up `PATH` and other environment variables for the current terminal. After calling these scripts, `emcc`, `clang`, etc. are all accessible from the command line.

**Check out the tutorial!** See the Emscripten [Tutorial](https://github.com/kripken/emscripten/wiki/Tutorial) page for help on how to get going with the tools from command line.

## SDK Concepts

The Emscripten SDK is effectively a small package manager for tools that are used in conjunction with Emscripten. The following glossary highlights the important concepts to help understanding the internals of the SDK:

* **Tool**: The basic unit of software bundled in the SDK. A Tool has a name and a version. For example, 'clang-3.2-32bit' is a Tool that contains the 32-bit version of the Clang v3.2 compiler.
* **SDK**: A set of tools. For example, 'sdk-1.5.6-32bit' is an SDK consisting of the tools `clang-3.2-32bit`, `node-0.10.17-32bit`, `python-2.7.5.1-32bit` and `emscripten-1.5.6`.
* **Active Tool/SDK**: Emscripten stores compiler configuration in a user-specific file **~/.emscripten**. This file points to paths for Emscripten, Python, Clang and so on. If the file ~/.emscripten is configured to point to a Tool in a specific directory, then that tool is denoted as being **active**. The Emscripten Command Prompt always gives access to the currently active Tools. This mechanism allows switching between different installed SDK versions easily.
* **emsdk**: This is the name of the manager script that Emscripten SDK is accessed through. Most operations are of the form `emsdk command`. To access the emsdk script, launch the Emscripten Command Prompt.

## SDK Maintenance

The following tasks are common with the Emscripten SDK:

##### How do I work the emsdk utility?

Run `emsdk help` or just `emsdk` to get information about all available commands.

##### How do I check the installation status and version of the SDK and tools?

To get a list of all currently installed tools and SDK versions, and all available tools, run `emsdk list`.
* A line will be printed for each tool/SDK that is available for installation.
* The text `INSTALLED` will be shown for each tool that has already been installed.
* If a tool/SDK is currently active, a star * will be shown next to it.
* If a tool/SDK is currently active, but the terminal your are calling emsdk from does not have `PATH` and environment set up to utilize that tool, a star in parentheses (*) will be shown next to it. Run `emsdk_env.bat` (Windows) or `source ./emsdk_env.sh` (Linux and OS X) to set up the environment for the calling terminal.

##### How do I install a tool/SDK version?

Run the command `emsdk install <tool/sdk name>` to download and install a new tool or an SDK version.

##### How do I remove a tool or an SDK?

Run the command `emsdk uninstall <tool/sdk name>` to delete the given tool or SDK from the local hard drive completely.

##### How do I check for updates to the Emscripten SDK?

The command `emsdk update` will fetch package information for all new tools and SDK versions. After that, run `emsdk install <tool/sdk name>` to install a new version. The command `emsdk update-tags` obtains a list of all new tagged releases from GitHub without updating Emscripten SDK itself.

##### How do I install an old Emscripten compiler version?

Emsdk contains a history of old compiler versions that you can use to maintain your migration path. Type `emsdk list --old` to get a list of archived tool and SDK versions, and `emsdk install <name_of_tool>` to install it.

On Windows, you can directly install an old SDK version by using one of the archived offline NSIS installers. See the **Archived Releases** section down below.

##### When working on git branches compiled from source, how do I update to a newer compiler version?

Unlike tags and precompiled versions, a few of the SDK packages are based on "moving" git branches and compiled from source (sdk-incoming, sdk-master, emscripten-incoming, emscripten-master, binaryen-master). Because of that, the compiled versions will eventually go out of date as new commits are introduced to the development branches. To update an old compiled installation of one of this branches, simply reissue the "emsdk install" command on that tool/SDK. This will `git pull` the latest changes to the branch and issue an incremental recompilation of the target in question. This way you can keep calling `emsdk install` to keep an Emscripten installation up to date with a given git branch.

Note though that if the previously compiled branch is very old, sometimes CMake gets confused and is unable to properly rebuild a project. This has happened in the past e.g. when LLVM migrated to requiring a newer CMake version. In cases of any odd compilation errors, it is advised to try deleting the intermediate build directory to clear the build (e.g. "emsdk/clang/fastcomp/build_xxx/") before reissuing `emsdk install`.

##### How do I change the currently active SDK version?

You can toggle between different tools and SDK versions by running `emsdk activate <tool/sdk name>`. Activating a tool will set up `~/.emscripten` to point to that particular tool. On Windows, you can pass the option `--global` to the `activate` command to register the environment permanently to the system registry for all users.

##### How do I build multiple projects with different SDK versions in parallel?

By default, Emscripten locates all configuration files in the home directory of the user. This may be a problem if you need to simultaneously build with multiple Emscripten compiler versions, since the user home directory can only be configured to point to one compiler at a time. This can be overcome by specifying the '--embedded' option as a parameter to 'emsdk activate', which will signal emsdk to generate the compiler configuration files inside the emsdk root directory instead of the user home directory. Use this option also when it is desirable to run emsdk in a fully portable mode that does not touch any files outside the emsdk directory.

##### How do I track the latest Emscripten development with the SDK?

A common and supported use case of the Emscripten SDK is to enable the workflow where you directly interact with the github repositories. This allows you to obtain new features and latest fixes immediately as they are pushed to the github repository, without having to wait for release to be tagged. You do not need a github account or a fork of Emscripten to do this. To switch to using the latest upstream git development branch `incoming`, run the following:

    emsdk install git-1.9.4 # Install git. Skip if the system already has it.
    emsdk install sdk-incoming-64bit # Clone+pull the latest kripken/emscripten/incoming.
    emsdk activate sdk-incoming-64bit # Set the incoming SDK as the currently active one.

If you want to use the upstream stable branch `master`, then replace `-incoming-` with `-master-` above.

##### How do I use my own Emscripten github fork with the SDK?

It is also possible to use your own fork of the Emscripten repository via the SDK. This is achieved with standard git machinery, so there if you are already acquainted with working on multiple remotes in a git clone, these steps should be familiar to you. This is useful in the case when you want to make your own modifications to the Emscripten toolchain, but still keep using the SDK environment and tools. To set up your own fork as the currently active Emscripten toolchain, first install the `sdk-incoming` SDK like shown in the previous section, and then run the following commands in the emsdk directory:

    cd emscripten/incoming
    # Add a git remote link to your own repository.
    git remote add myremote https://github.com/mygituseraccount/emscripten.git
    # Obtain the changes in your link.
    git fetch myremote
    # Switch the emscripten-incoming tool to use your fork.
    git checkout -b myincoming --track myremote/incoming

In this way you can utilize the Emscripten SDK tools while using your own git fork. You can switch back and forth between remotes via the `git checkout` command as usual.

##### How do I use Emscripten SDK with a custom version of python, java, node.js or some other tool?

The provided Emscripten SDK targets are metapackages that refer to a specific set of tools that have been tested to work together. For example, `sdk-1.35.0-64bit` is an alias to the individual packages `clang-e1.35.0-64bit`, `node-4.1.1-64bit`, `python-2.7.5.3-64bit` and `emscripten-1.35.0`. This means that if you install this version of the SDK, both python and node.js will be installed inside emsdk as well. If you want to use your own/system python or node.js instead, you can opt to install emsdk by specifying the individual set of packages that you want to use. For example, `emsdk install clang-e1.35.0-64bit emscripten-1.35.0` will only install the Emscripten LLVM/Clang compiler and the Emscripten frontend without supplying python and node.js.

##### My installation fails with "fatal error: ld terminated with signal 9 [Killed]"?

This may happen if the system runs out of memory. If you are attempting to build one of the packages from source and are running in a virtual OS or have relatively little RAM and disk space available, then the build might fail. Try feeding your computer more memory. Another thing to try is to force emsdk install to build in a singlethreaded mode, which will require less RAM simultaneously. To do this, pass the `-j1` flag to the `emsdk install` command.

## Uninstalling the Emscripten SDK

If you installed the SDK using an NSIS installer on Windows, launch 'Control Panel' -> 'Uninstall a program' -> 'Emscripten SDK'.

If you want to remove a Portable SDK, just delete the directory where you put the Portable SDK into.

## Platform-Specific Notes

##### Mac OS X

* On OS X (and Linux), the git tool will not be installed automatically. Git is not a required core component, and is only needed if you want to use one of the development branches emscripten-incoming or emscripten-master directly, instead of the fixed releases. To install git on OS X, you can

  1. Install XCode, and in XCode, install XCode Command Line Tools. This will provide git to the system PATH. For more help on this step, see http://stackoverflow.com/questions/9329243/xcode-4-4-command-line-tools
  2. Install git directly from http://git-scm.com/

* Also, on OS X, `java` is not bundled with the Emscripten SDK. After installing emscripten via emsdk, typing 'emcc --help' should pop up a OS X dialog "Java is not installed. To open java, you need a Java SE 6 runtime. Would you like to install one now?" that will automatically download a Java runtime to the system.

##### Linux

* On Linux, emsdk does not interact with Linux package managers on the behalf of the user, nor does it install any tools to the system. All file changes are done inside the `emsdk/` directory.

* Emsdk does not provide `python`, `node` or `java` on Linux. The user is expected to install these beforehand with the system package manager.

##### Windows

* On Windows, if you want to build any of the packages from source (instead of using the precompiled ones), you will need git, CMake and Visual Studio 2015. Git can be installed via emsdk by typing "emsdk install git-1.9.4", CMake can be found from http://www.cmake.org/, and Visual Studio can be installed from https://www.visualstudio.com.

###### How do I run Emscripten on 32-bit Windows?

Emscripten SDK releases are no longer packaged or maintained for 32-bit Windows. If you want to run Emscripten on a 32-bit system, you can try manually building the compiler for 32-bit mode. Follow the steps in the above section "Building an Emscripten tag or branch from source" to get started.

### Archived Releases

You can always install old SDK and compiler toolchains via the latest emsdk. If you need to fall back to an old version, download the Portable SDK version and use that to install a previous version of a tool. All old tool versions are available by typing `emsdk list --old`.

On Windows, you can install one of the **old versions** via an offline NSIS installer:

 - [emsdk-1.5.6.1-full.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.5.6.1-full.exe) (32-bit, first emsdk release)
 - [emsdk-1.5.6.2-full-32bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.5.6.2-full-32bit.exe)
 - [emsdk-1.5.6.2-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.5.6.2-full-64bit.exe)
 - [emsdk-1.7.8-full-32bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.7.8-full-32bit.exe)
 - [emsdk-1.7.8-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.7.8-full-64bit.exe)
 - [emsdk-1.8.2-full-32bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.8.2-full-32bit.exe)
 - [emsdk-1.8.2-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.8.2-full-64bit.exe)
 - [emsdk-1.12.0-full-32bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.12.0-full-32bit.exe)
 - [emsdk-1.12.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.12.0-full-64bit.exe) (the last non-fastcomp version with Clang 3.2)
 - [emsdk-1.13.0-full-32bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.13.0-full-64bit.exe) (a unstable first fastcomp release with Clang 3.3)
 - [emsdk-1.16.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.16.0-full-64bit.exe) (first stable fastcomp release)
 - [emsdk-1.21.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.21.0-full-64bit.exe)
 - [emsdk-1.22.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.22.0-full-64bit.exe)
 - [emsdk-1.25.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.25.0-full-64bit.exe)
 - [emsdk-1.27.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.27.0-full-64bit.exe) (last release based on Clang 3.3)
 - [emsdk-1.29.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.29.0-full-64bit.exe) (the only release based on Clang 3.4)
 - [emsdk-1.30.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.30.0-full-64bit.exe) (the only release based on Clang 3.5)
 - [emsdk-1.34.1-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.34.1-full-64bit.exe) (first release based on Clang 3.7)
 - [emsdk-1.35.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.35.0-full-64bit.exe)
 - [emsdk-1.35.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.35.0-full-64bit.exe)
 - [emsdk-1.35.0-web-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.35.0-web-64bit.exe)
 - [emsdk-1.35.0-portable-64bit.zip](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.35.0-portable-64bit.zip)

Snapshots of all tagged Emscripten compiler releases (not full SDKs) can be found at [emscripten/releases](https://github.com/kripken/emscripten/releases).
