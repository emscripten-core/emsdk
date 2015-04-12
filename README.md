# Emscripten SDK

The whole Emscripten toolchain is distributed as a standalone Emscripten SDK. The SDK provides all the required tools, such as Clang, Python, Node.js and Visual Studio integration along with an update mechanism that enables migrating to newer Emscripten versions as they are released.

You can also set up Emscripten from source, without the pre-built SDK, see "Installing from Source" below.

## Downloads

To get started with Emscripten development, grab one of the packages below:

Windows:
* Emscripten SDK Web Installer is a NSIS installer that always gets you the latest Emscripten SDK from the web:
  * [emsdk-1.30.0-web-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.30.0-web-64bit.exe)
* Emscripten SDK Offline Installer is a NSIS installer that bundles together the Emscripten toolchain as an offline-installable package:
  * [emsdk-1.30.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.30.0-full-64bit.exe)
* Portable Emscripten SDK is a zipped package of the Emscripten SDK that does not require system installation privileges. Just unzip and go:
  * [emsdk-1.30.0-portable-64bit.zip](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.30.0-portable-64bit.zip)

Linux and Mac OS X:
* [emsdk-portable.tar.gz](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-portable.tar.gz): Emscripten SDK is available as a portable web-installer for Linux and OS X.

**Old Releases** are available in the **Archived Releases** section below. 

## Installation Instructions

Check one of the topics below for what to do with the package you just downloaded.

#### Windows: Installing using a NSIS Installer

The NSIS installers register the Emscripten SDK as a 'standard' Windows application. To install the SDK, download a NSIS .exe file above, double-click on it, and run through the installer to perform the installation. After the installer finishes, the full Emscripten toolchain will be available in the directory that was chosen during the installation, and no other steps are necessary. If your system has Visual Studio 2010 installed, the vs-tool MSBuild plugin will be automatically installed as well.

#### Windows, OSX and Linux: Installing the Portable SDK

The Portable Emscripten SDK is a no-installer version of the SDK package. It is identical to the NSIS installer, except that it does not interact with the Windows registry, which allows Emscripten to be used on a computer without administrative privileges, and gives the ability to migrate the installation from one location (directory or computer) to another by just copying/zipping up the directory contents.

If you want to use the Portable Emscripten SDK, the initial setup process is as follows:

1. Download and unzip the portable SDK package to a directory of your choice. This directory will contain the Emscripten SDK.
2. Open a command prompt to the directory of the SDK.
3. Run `emsdk update`. This will fetch the latest registry of available tools.
4. Run `emsdk install latest`. This will download and install the latest SDK tools.
5. Run `emsdk activate latest`. This will set up ~/.emscripten to point to the SDK.

Whenever you change the location of the Portable SDK (e.g. take it to another computer), re-run step 5.

Note: On Linux and OSX, type `./emsdk` instead of `emsdk` above.

### Installing from Source

If you want to build Emscripten Clang backend and the dependencies yourself, follow the instructions in this section.

Get the following:

 * The Emscripten code, from github (git clone git://github.com/kripken/emscripten.git. The master branch is fine, it is guaranteed to always be stable. We merge to master only after all tests pass.)
 * Emscripten's LLVM and Clang. Emscripten now has an LLVM backend ("fastcomp"), which means you need to use our LLVM+Clang. See "[Getting Fastcomp](https://github.com/kripken/emscripten/wiki/LLVM-Backend#getting-fastcomp)" in the [LLVM Backend](https://github.com/kripken/emscripten/wiki/LLVM-Backend) page. (See also notes on that link about how to disable fastcomp and use a stock version of LLVM, if you want, although that is not recommended.)
 * Node.js (0.8 or above; 0.10.17 or above to run websocket-using servers in node)
 * Python 2.7.3
 * Optionally, if you want to use Closure Compiler to minify your code as much as possible, you will also need Java.

The [LLVM Backend](https://github.com/kripken/emscripten/wiki/LLVM-Backend) page has instructions for building Emscripten's LLVM+Clang. After you build it, run `emcc -v`, which should print out the version number as well as run some basic tests.

Additional Notes:

 * Python is probably already installed if you are on Linux or OS X.
 * Node.js and LLVM should have convenient binaries for your OS, but installing them from source is easy, just compile them in their directories, you don't need to bother with installing them systemwide.

## Getting Started with Emscripten

The tools in the Emscripten toolchain can be accessed in various ways. Which one you use depends on your preference.

##### Command line usage

The Emscripten compiler is available on the command line by invoking `emcc` or `em++`. They are located in the folder `emsdk/emscripten/<version>/` in the SDK.

The root directory of the Emscripten SDK contains scripts `emsdk_env.bat` (Windows) and `emsdk_env.sh` (Linux, OSX) which set up `PATH` and other environment variables for the current terminal. After calling these scripts, `emcc`, `clang`, etc. are all accessible from the command line.

<b>Check out the tutorial!</b> See the Emscripten [Tutorial](https://github.com/kripken/emscripten/wiki/Tutorial) page for help on how to get going with the tools from command line.

##### Windows: Emscripten Command Prompt

Start the Emscripten Command Prompt from Start Menu -> All Programs -> Emscripten -> Emscripten Command Prompt. This will spawn a new command prompt that has all the tools for the currently activated SDK version set to PATH. The Emscripten Command Prompt is analogous to the Visual Studio Command Prompt that ships with installations of Visual Studio.

##### Windows: Use Visual Studio 2010

After installing the vs-tool plugin, a new 'Emscripten' platform will appear to the list of all Solution Platforms in Visual Studio. To activate the Emscripten platform, right-click on the solution in the Solution Explorer, choose Configuration Manager... -> Active solution platform... -> New... -> Emscripten. After that, activating the Emscripten platform for the solution will make Visual Studio run the project build through Emscripten, producing .html or .js output, depending on the project properties you set up.

Note: If you copied the Emscripten platform properties from the Win32 platform, be sure to go and clean up any leftover Win32-specific #defines and other configuration from the Emscripten platform!

## SDK Concepts

The Emscripten SDK is effectively a small package manager for tools that are used in conjunction with Emscripten. The following glossary highlights the important concepts to help understanding the internals of the SDK:

* <b>Tool</b>: The basic unit of software bundled in the SDK. A Tool has a name and a version. For example, 'clang-3.2-32bit' is a Tool that contains the 32-bit version of the Clang v3.2 compiler.
* <b>SDK</b>: A set of tools. For example, 'sdk-1.5.6-32bit' is an SDK consisting of the tools clang-3.2-32bit, node-0.10.17-32bit, python-2.7.5.1-32bit and emscripten-1.5.6.
* <b>Active Tool/SDK</b>: Emscripten stores compiler configuration in a user-specific file <b>~/.emscripten</b>. This file points to paths for Emscripten, Python, Clang and so on. If the file ~/.emscripten is configured to point to a Tool in a specific directory, then that tool is denoted as being <b>active</b>. The Emscripten Command Prompt always gives access to the currently active Tools. This mechanism allows switching between different SDK versions easily.
* <b>emsdk</b>: This is the name of the manager script that Emscripten SDK is accessed through. Most operations are of the form `emsdk command`. To access the emsdk script, launch the Emscripten Command Prompt.

## SDK Maintenance

The following tasks are common with the Emscripten SDK:

##### How do I work the emsdk utility?

Run `emsdk help` or just `emsdk` to get information about all available commands.

##### How do I check the installation status and version of the SDK and tools?

To get a list of all currently installed tools and SDK versions, and all available tools, run `emsdk list`.
* A line will be printed for each tool/SDK that is available for installation.
* The text `INSTALLED` will be shown for each tool that has already been installed.
* If a tool/SDK is currently active, a star * will be shown next to it.
* If a tool/SDK is currently active, but the terminal your are calling emsdk from does not have `PATH` and environment set up to utilize that tool, a star in parentheses (*) will be shown next to it. Run `emsdk_env.bat` (Windows) or `source ./emsdk_env.sh` (Linux and OSX) to set up the environment for the calling terminal.

##### How do I install a tool/SDK version?

Run the command `emsdk install <tool/sdk name>` to download and install a new tool or an SDK version.

##### How do I remove a tool or an SDK?

Run the command `emsdk uninstall <tool/sdk name>` to delete the given tool or SDK from the local harddrive completely.

##### How do I check for updates to the Emscripten SDK?

The command `emsdk update` will fetch package information for all new tools and SDK versions. After that, run `emsdk install <tool/sdk name>` to install a new version.

##### How do I install an old Emscripten compiler version?

Emsdk contains a history of old compiler versions that you can use to maintain your migration path. Type `emsdk list --old` to get a list of archived tool and SDK versions, and `emsdk install <name_of_tool>` to install it.

On Windows, you can directly install an old SDK version by using one of the archived offline NSIS installers. See the **Archived Releases** section down below.

##### How do I change the currently active SDK version?

You can toggle between different tools and SDK versions by running `emsdk activate <tool/sdk name>`. Activating a tool will set up `~/.emscripten` to point to that particular tool. On Windows, you can pass the option `--global` to the `activate` command to register the environment permanently to the system registry for all users.

##### How do I build multiple projects with different SDK versions in parallel?

By default, Emscripten locates all configuration files in the home directory of the user. This may be a problem if you need to simultaneously build with multiple Emscripten compiler versions, since the user home directory can only be configured to point to one compiler at a time. This can be overcome by specifying the '--embedded' option as a parameter to 'emsdk activate', which will signal emsdk to generate the compiler configuration files inside the emsdk root directory instead of the user home directory. Use this option also when it is desirable to run emsdk in a fully portable mode that does not touch any files outside the emsdk directory.

##### How do I track the latest Emscripten development with the SDK?

A common and supported use case of the Emscripten SDK is to enable the workflow where you directly interact with the github repositories. This allows you to obtain new features and latest fixes immediately as they are pushed to the github repository, without having to wait for release to be tagged. You do not need a github account or a fork of Emscripten to do this. To switch to using the latest upstream git development branch `incoming`, run the following:

    emsdk install git-1.8.3 # Install git. Skip if the system already has it.
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

## Uninstalling the Emscripten SDK

If you installed the SDK using a NSIS installer on Windows, launch 'Control Panel' -> 'Uninstall a program' -> 'Emscripten SDK'.

If you want to remove a Portable SDK, just delete the directory where you put the Portable SDK into.

## Platform-Specific Notes

##### Mac OS X

* On OSX (and Linux), the git tool will not be installed automatically. Git is not a required core component, and is only needed if you want to use one of the development branches emscripten-incoming or emscripten-master directly, instead of the fixed releases. To install git on OSX, you can

  1. Install XCode, and in XCode, install XCode Command Line Tools. This will provide git to the system PATH. For more help on this step, see http://stackoverflow.com/questions/9329243/xcode-4-4-command-line-tools
  2. Install git directly from http://git-scm.com/

* Also, on OSX, `java` is not bundled with the Emscripten SDK. After installing emscripten via emsdk, typing 'emcc --help' should pop up a OSX dialog "Java is not installed. To open java, you need a Java SE 6 runtime. Would you like to install one now?" that will automatically download a Java runtime to the system.

* Emscripten requires the command line tool 'python2' to be present on OSX. On default OSX installations, this does not exist. To manually work around this issue, see step 10 at https://github.com/kripken/emscripten/wiki/Getting-started-on-Mac-OS-X

##### Linux

* On Linux, prebuilt binaries of tools are not available. Installing a tool will automatically clone and build that tool from the sources inside emsdk directory. Emsdk does not interact with Linux package managers on the behalf of the user, nor does it install any tools to the system. All file changes are done inside the `emsdk/` directory.

* Because emsdk builds software from the source on Linux, the system must have a working compiler environment available.

* Emsdk does not provide `python`, `node` or `java` on Linux. The user is expected to install these beforehand with the system package manager.

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
 - [emsdk-1.29.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.29.0-full-64bit.exe) (first and last release based on Clang 3.4)
 - [emsdk-1.30.0-full-64bit.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.30.0-full-64bit.exe) (first and last release based on Clang 3.5)
