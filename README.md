# Emscripten SDK

The whole Emscripten toolchain is distributed as a standalone Emscripten SDK. The SDK provides all the required tools, such as Clang, Python, Node.js and Visual Studio integration along with an update mechanism that enables migrating to newer Emscripten versions as they are released.

## Downloads

To get started with Emscripten development, grab one of the packages below:

Windows:
* [emsdk-webinstall.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-webinstall.exe): Emscripten SDK Web Installer is a NSIS installer that always gets you the latest Emscripten SDK from the web.
* [emsdk-1.5.6.1-full.exe](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-1.5.6.1-full.exe): Emscripten SDK 1.5.6.1 Offline Installer is a NSIS installer that bundles together the Emscripten toolchain as an offline-installable package.
* [emsdk-portable.zip](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-portable.zip): Portable Emscripten SDK is a web-install version of the Emscripten SDK that does not require system installation privileges.

Mac OS X:
* [emsdk-portable.tar.gz](https://s3.amazonaws.com/mozilla-games/emscripten/releases/emsdk-portable.tar.gz): Emscripten SDK is available as a portable web-installer for OS X.

Linux:
* See the instructions section below.

## Installation Instructions

Check one of the topics below for what to do with the package you just downloaded.

#### Windows: Installing using a NSIS Installer

The NSIS installers register the Emscripten SDK as a 'standard' Windows application. To install the SDK, download a NSIS .exe file above, double-click on it, and run through the installer to perform the installation. After the installer finishes, the full Emscripten toolchain will be available in the directory that was chosen during the installation, and no other steps are necessary. If your system has Visual Studio 2010 installed, the vs-tool MSBuild plugin will be automatically installed as well.

#### Windows and OSX: Installing the Portable SDK

The Portable Emscripten SDK is a no-installer version of the SDK package. It is identical to the NSIS installer, except that it does not interact with the Windows registry, which allows Emscripten to be used on a computer without administrative privileges, and gives the ability to migrate the installation from one location (directory or computer) to another by just copying/zipping up the directory contents.

If you want to use the Portable Emscripten SDK, the initial setup process is as follows:

1. Download and unzip the portable SDK package to a directory of your choice. This directory will contain the Emscripten SDK.
2. Open a command prompt to the directory of the SDK.
3. Run `emsdk update`. This will fetch the latest registry of available tools.
4. Run `emsdk install latest`. This will download and install the latest SDK tools.
5. Run `emsdk activate latest`. This will set up ~/.emscripten to point to the SDK.

Whenever you change the location of the Portable SDK (e.g. take it to another computer), re-run step 5.

Note: On OSX, type `./emsdk` instead of `emsdk` above.

#### Windows and OSX: Build the Emscripten toolchain manually

If you do not want to use the SDK, there exists guides for setting up Emscripten and its prerequisites manually, see

* [Build Clang on Mac OS X](https://github.com/kripken/emscripten/wiki/Getting-started-on-Mac-OS-X).
* [Download a prebuilt Clang on Mac OS X](https://gist.github.com/dweekly/5873953).
* [Get Emscripten and Clang via brew](https://gist.github.com/nathanhammond/1974955) by nathanhammond.
* [Manual Emscripten setup on Windows](https://github.com/kripken/emscripten/wiki/Using-Emscripten-on-Windows).

#### Linux

The SDK is not available for Linux at the moment. To get started on Linux, see one of the following guides for a manual setup:
* For help on Ubuntu, you can follow the [Getting Started on Ubuntu 12.10](https://github.com/kripken/emscripten/wiki/Getting-Started-on-Ubuntu-12.10) guide for instructions on how to obtain the prerequisites and build Clang manually using CMake.
* For help on Debian, see this [guide by EarthServer](https://earthserver.com/Setting_up_emscripten_development_environment_on_Linux).
* rhelmer has provided a Vagrant VM for Emscripten, see [emscripten-vagrant](https://github.com/rhelmer/emscripten-vagrant).
* Dirk Krause created an [Amazon EC2 image](https://groups.google.com/forum/?fromgroups=#!topic/emscripten-discuss/H8kG0kP1eDE) for Emscripten.

<b>Important!</b> Emscripten is very specific about the versions of Clang it supports! Currently Clang 3.2 is being used, building a newer version can have some issues!

## Getting Started with Emscripten

The tools in the Emscripten toolchain can be accessed in various ways. Which one you use depends on your preference.

##### Command line usage

The Emscripten compiler is available on the command line by invoking `emcc` or `em++`. They are located in the folder `emsdk/emscripten/<version>/` in the SDK. You can add this directory to PATH to get an easy access to the toolchain.

<b>Check out the tutorial!</b> See the Emscripten [Tutorial](https://github.com/kripken/emscripten/wiki/Tutorial) page for help on how to get going with the tools from command line.

##### Windows: Emscripten Command Prompt

Start the Emscripten Command Prompt from Start Menu -> All Programs -> Emscripten -> Emscripten Command Prompt. This will spawn a new command prompt that has all the tools for the currently activated SDK version set to PATH. The Emscripten Command Prompt is analogous to the Visual Studio Command Prompt that ships with installations of Visual Studio.

##### Windows: Use Visual Studio 2010

After installing the vs-tool plugin, a new 'Emscripten' configuration will appear to the list of all Solution Configurations in Visual Studio. Activating that configuration for a solution/project will make Visual Studio run the project build through Emscripten, producing .html or .js output, depending on the project properties you set up.

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
* If a tool/SDK is currently active, a star (*) will be shown next to it.

##### How do I install a tool/SDK version?

Run the command `emsdk install <tool/sdk name>` to download and install a new tool or an SDK version.

##### How do I remove a tool or an SDK?

Run the command `emsdk uninstall <tool/sdk name>` to delete the given tool or SDK from the local harddrive completely.

##### How do I check for updates to the Emscripten SDK?

The command `emsdk update` will fetch package information for all new tools and SDK versions. After that, run `emsdk install <tool/sdk name>` to install a new version.

##### How do I change the currently active SDK version?

You can toggle between different tools and SDK versions by running `emsdk activate <tool/sdk name>`.

## Uninstalling the Emscripten SDK

If you installed the SDK using a NSIS installer on Windows, launch 'Control Panel' -> 'Uninstall a program' -> 'Emscripten SDK'.

If you want to remove a Portable SDK, just delete the directory where you put the Portable SDK into.

## Platform-Specific Notes

##### Mac OS X

* On OSX, the git tool will not be installed automatically. Git is not a required core component, and is only needed if you want to use one of the development branches emscripten-incoming or emscripten-master directly, instead of the fixed releases. To install git on OSX, you can

	1. Install XCode, and in XCode, install XCode Command Line Tools. This will provide git to the system PATH. For more help on this step, see http://stackoverflow.com/questions/9329243/xcode-4-4-command-line-tools
	2. Install git directly from http://git-scm.com/

* Also, on OSX, java is not bundled with the Emscripten SDK. After installing emscripten via emsdk, typing 'emcc --help' should pop up a OSX dialog "Java is not installed. To open java, you need a Java SE 6 runtime. Would you like to install one now?" that will automatically download a Java runtime to the system.

* Emscripten requires the command line tool 'python2' to be present on OSX. On default OSX installations, this does not exist. To manually work around this issue, see step 10 at https://github.com/kripken/emscripten/wiki/Getting-started-on-Mac-OS-X

##### Windows

* Whereas OSX only ships 64-bit executables of the toolchain, on Windows the 32-bit version of the toolchain is available. This is due to a detected incompatibility with Visual Studio 2010 and 64-bit tools.
