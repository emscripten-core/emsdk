Emscripten SDK
==============

To make it quick and easy to set up and maintain an Emscripten development environment, the whole Emscripten toolchain is available as a standalone Emscripten SDK. The SDK provides all the required tools, such as Clang, python node.js and Visual Studio integration along with an update mechanism that makes it simple to migrate to newer Emscripten versions as they are released.

Get the SDK
-----------

To get started with Emscripten development quickly and hassle-free, grab one of the packages below:

Windows:
* [emsdk-webinstall.exe](http://clb.demon.fi/emscripten/releases/emsdk-webinstall.exe): Emscripten SDK Web Installer is a NSIS installer that always gets you the latest Emscripten SDK from the web.
* [emsdk-1.5.6-full.exe](http://clb.demon.fi/emscripten/releases/emsdk-1.5.6-full.exe): Emscripten SDK 1.5.6 Offline Installer is a NSIS installer that bundles together the Emscripten 1.5.6 toolchain as an offline-installable package.
* [emsdk-portable.zip](http://clb.demon.fi/emscripten/releases/emsdk-portable.zip): Portable Emscripten SDK is a portable version of the Emscripten SDK that does not require system installation privileges.

Note: Currently the Emscripten SDK is Windows-only, but it is being developed with the goal in mind of extending it to OSX and possibly Linux as well.

Installing using the NSIS Installer
-----------------------------------

The NSIS installers register the Emscripten SDK as a 'standard' Windows application. To install the SDK, download a NSIS .exe file above, double-click on it, and run through the installer to perform the installation. After the installer finishes, the full Emscripten toolchain will be available in the directory that was chosen during the installation, and no other steps are necessary. If your system has Visual Studio 2010 installed, the vs-tool MSBuild plugin will be automatically installed as well.

Installing the Portable SDK
---------------------------

The Portable Emscripten SDK is a no-installer version of the SDK package. It is identical to the NSIS installer, except that it does not interact with the Windows registry, which allows Emscripten to be used on a computer without administrative privileges, and the ability to migrate the installation from one location (directory or computer) to another by just copying/zipping up the directory contents.

If you want to use the Portable Emscripten SDK, the initial setup process is as follows:

1. Unzip the SDK to a directory of your choice. This directory will contain the Emscripten SDK.
2. Open a command prompt to the directory of the SDK.
3. Run `emsdk update`. This will fetch the latest registry of available tools.
4. Run `emsdk install latest`. This will download and install the latest SDK tools.
5. Run `emsdk activate latest`. This will set up ~/.emscripten to point to the SDK.

Whenever you change the location of the Portable SDK (e.g. take it to another computer), re-run step 5.

SDK Concepts
------------

The Emscripten SDK is effectively a small package manager for tools that are used in conjunction with Emscripten. The following glossary highlights the important concepts to help understanding the internals of the SDK:

* <b>Tool</b>: The basic unit of software bundled in the SDK. A Tool has a name and a version. For example, 'clang-3.2-32bit' is a Tool that contains the 32-bit version of the Clang v3.2 compiler.
* <b>SDK</b>: A set of tools. For example, 'sdk-1.5.6-32bit' is an SDK consisting of the tools clang-3.2-32bit, node-0.10.17-32bit, python-2.7.5.1-32bit and emscripten-1.5.6.
* <b>Active Tool/SDK</b>: Emscripten stores compiler configuration in a user-specific file <b>~/.emscripten</b>. This file points to paths for Emscripten, Python, Clang and so on. If the file ~/.emscripten is configured to point to a Tool in a specific directory, then that tool is denoted as being <b>active</b>. The Emscripten Command Prompt always gives access to the currently active Tools. This mechanism allows switching between different SDK versions easily.
* <b>emsdk</b>: This is the name of the manager script that Emscripten SDK is accessed through. Most operations are of the form `emsdk command`. To access the emsdk script, launch the Emscripten Command Prompt.

Using the SDK
-------------

The tools in the Emscripten SDK can be accessed in various ways. Which one you use depends only on your preference.

##### Emscripten Command Prompt

Start the Emscripten Command Prompt from Start Menu -> All Programs -> Emscripten -> Emscripten Command Prompt. This will spawn a new command prompt that has all the tools for the currently activated SDK version set to PATH. The Emscripten Command Prompt is analogous to the Visual Studio Command Prompt that ships with installations of Visual Studio.

##### Global PATH Setup

If you would prefer that all command prompts in the system should have the Emscripten SDK tools in PATH, you can of course add them manually. Start the Emscripten Command Prompt to display an info line of all paths that should be added.

##### Use Visual Studio 2010

After installing the vs-tool plugin, a new 'Emscripten' configuration will appear to the list of all Solution Configurations in Visual Studio. Activating that configuration for a solution/project will make Visual Studio run the project build through Emscripten, producing .html or .js output, depending on the project properties you set up.

SDK Maintenance
---------------

The following tasks are common with the Emscripten SDK:

##### How do I work the emsdk utility?

Run `emsdk help` or just `emsdk` to get information about all available commands.

##### How do I check the installation status and version of the SDK and tools?

To get a list of all currently installed tools and SDK versions, and all available tools, run `emsdk list`.
* A line will be printed for each tool/SDK that is available for installation.
* The text `INSTALLED` will be shown for each tool that is available for install.
* If a tool/SDK is currently active, a star (*) will be shown next to it.

##### How do I install a tool/SDK version?

Run the command `emsdk install <tool/sdk name>` to download and install a new tool or an SDK version.

##### How do I remove a tool or an SDK?

Run the command `emsdk uninstall <tool/sdk name>` to delete the given tool or SDK from the local harddrive completely.

##### How do I check for updates to the Emscripten SDK?

The command `emsdk update` will fetch package information for all new tools and SDK versions. After that, run `emsdk install <tool/sdk name>` to install a new version.

##### How do I change the currently active SDK version?

You can toggle between different tools and SDK versions by running `emsdk activate <tool/sdk name>`.

Uninstalling the Emscripten SDK
-------------------------------

If you installed the SDK using a NSIS installer, launch 'Control Panel' -> 'Uninstall a program' -> 'Emscripten SDK'.

If you want to remove a Portable SDK, just delete the directory where you put the Portable SDK into.

Platform-Specific Notes
-----------------------

##### Mac OS X

* On OSX, the git tool will not be installed automatically. Git is not a required core component, and is only needed if you want to use one of the development branches emscripten-incoming or emscripten-master directly, instead of the fixed releases. To install git on OSX, you can

	1. Install XCode, and in XCode, install XCode Command Line Tools. This will provide git to the system PATH. For more help on this step, see http://stackoverflow.com/questions/9329243/xcode-4-4-command-line-tools
	2. Install git directly from http://git-scm.com/

* Also, on OSX, java is not bundled with the Emscripten SDK. After installing emscripten via emsdk, typing 'emcc --help' should pop up a OSX dialog "Java is not installed. To open java, you need a Java SE 6 runtime. Would you like to install one now?" that will automatically download a Java runtime to the system.

* Emscripten requires the command line tool 'python2' to be present on OSX. On default OSX installations, this does not exist. To manually work around this issue, see step 10 at https://github.com/kripken/emscripten/wiki/Getting-started-on-Mac-OS-X

##### Windows

* Whereas OSX and Linux tools only ship 64-bit executables of the toolchain, on Windows the 32-bit version of the toolchain is available. This is due to a detected incompatibility with Visual Studio 2010 and 64-bit tools.
