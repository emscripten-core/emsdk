#!/usr/bin/env python
# Copyright 2019 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

from __future__ import print_function

import copy
import errno
import json
import multiprocessing
import os
import os.path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

if sys.version_info >= (3,):
  from urllib.parse import urljoin
  from urllib.request import urlopen
  import functools
else:
  from urlparse import urljoin
  from urllib2 import urlopen

# EMSDK_DEV is a developer mode flag, which, if true, the SDK is downloaded from a 'staging' online source,
# instead of the public source. New releases are first deployed to the staging source for testing, before
# being published to the public. Don't enable this unless you develop EMSDK itself and need to access the
# staging source repository instead.
EMSDK_DEV = bool(os.getenv('EMSDK_DEV')) if os.getenv('EMSDK_DEV') is not None else False

if EMSDK_DEV:
  print('EMSDK_DEV active.')
  emsdk_master_server = 'http://clb.demon.fi/emscripten_dev/packages/'
else:
  emsdk_master_server = 'https://storage.googleapis.com/webassembly/emscripten-releases-builds/deps/'

emsdk_packages_url = emsdk_master_server

emscripten_releases_repo = 'https://chromium.googlesource.com/emscripten-releases'

emscripten_releases_download_url_template = "https://storage.googleapis.com/webassembly/emscripten-releases-builds/%s/%s/wasm-binaries.%s"

emsdk_zip_download_url = 'https://github.com/emscripten-core/emsdk/archive/master.zip'

zips_subdir = 'zips/'

# Enable this to do very verbose printing about the different steps that are being run. Useful for debugging.
VERBOSE = int(os.getenv('EMSDK_VERBOSE', '0'))
TTY_OUTPUT = not os.getenv('EMSDK_NOTTY', not sys.stdout.isatty())

POWERSHELL = bool(os.getenv('EMSDK_POWERSHELL'))

WINDOWS = False
if os.name == 'nt' or (os.getenv('SYSTEMROOT') is not None and 'windows' in os.getenv('SYSTEMROOT').lower()) or (os.getenv('COMSPEC') is not None and 'windows' in os.getenv('COMSPEC').lower()):
  WINDOWS = True
  ENVPATH_SEPARATOR = ';'

MSYS = False
if os.getenv('MSYSTEM'):
  MSYS = True
  if os.getenv('MSYSTEM') != 'MSYS' and os.getenv('MSYSTEM') != 'MINGW64':
    print('Warning: MSYSTEM environment variable is present, and is set to "' + os.getenv('MSYSTEM') + '". This shell has not been tested with emsdk and may not work.') # https://stackoverflow.com/questions/37460073/msys-vs-mingw-internal-environment-variables

OSX = False
if platform.mac_ver()[0] != '':
  OSX = True
  ENVPATH_SEPARATOR = ':'

LINUX = False
if not OSX and (platform.system() == 'Linux' or os.name == 'posix'):
  LINUX = True
  ENVPATH_SEPARATOR = ':'

UNIX = (OSX or LINUX)

ARCH = 'unknown'
# platform.machine() may return AMD64 on windows, so standardize the case.
machine = platform.machine().lower()
if machine.startswith('x64') or machine.startswith('amd64') or machine.startswith('x86_64'):
  ARCH = 'x86_64'
elif machine.endswith('86'):
  ARCH = 'x86'
elif machine.startswith('aarch64') or machine.lower().startswith('arm64'):
  ARCH = 'aarch64'
elif platform.machine().startswith('arm'):
  ARCH = 'arm'
else:
  print("Warning: unknown machine architecture " + machine)
  print()

# Don't saturate all cores to not steal the whole system, but be aggressive.
CPU_CORES = int(os.environ.get('EMSDK_NUM_CORES', max(multiprocessing.cpu_count() - 1, 1)))

CMAKE_BUILD_TYPE_OVERRIDE = None

# If true, perform a --shallow clone of git.
GIT_CLONE_SHALLOW = False

# If true, LLVM backend is built with tests enabled, and Binaryen is built with Visual Studio static analyzer enabled.
BUILD_FOR_TESTING = False

# If 'auto', assertions are decided by the build type (Release&MinSizeRel=disabled, Debug&RelWithDebInfo=enabled)
# Other valid values are 'ON' and 'OFF'
ENABLE_LLVM_ASSERTIONS = 'auto'


def os_name():
  if WINDOWS:
    return 'win'
  elif LINUX:
    return 'linux'
  elif OSX:
    return 'osx'
  else:
    raise Exception('unknown OS')


def os_name_for_emscripten_releases():
  if WINDOWS:
    return 'win'
  elif LINUX:
    return 'linux'
  elif OSX:
    return 'mac'
  else:
    raise Exception('unknown OS')


def debug_print(msg, **args):
  if VERBOSE:
    print(msg, **args)


def to_unix_path(p):
  return p.replace('\\', '/')


def emsdk_path():
  return to_unix_path(os.path.dirname(os.path.realpath(__file__)))


emscripten_config_directory = os.path.expanduser("~/")
# If .emscripten exists, we are configuring as embedded inside the emsdk directory.
if os.path.exists(os.path.join(emsdk_path(), '.emscripten')):
  emscripten_config_directory = emsdk_path()

EMSDK_SET_ENV = 'emsdk_set_env.ps1' if POWERSHELL else 'emsdk_set_env.bat' if (WINDOWS and not MSYS) else 'emsdk_set_env.sh'

ARCHIVE_SUFFIXES = ('zip', '.tar', '.gz', '.xz', '.tbz2', '.bz2')


# Finds the given executable 'program' in PATH. Operates like the Unix tool 'which'.
def which(program):
  def is_exe(fpath):
    return os.path.isfile(fpath) and (WINDOWS or os.access(fpath, os.X_OK))

  fpath, fname = os.path.split(program)
  if fpath:
    if is_exe(program):
      return program
  else:
    for path in os.environ["PATH"].split(os.pathsep):
      path = path.strip('"')
      exe_file = os.path.join(path, program)
      if is_exe(exe_file):
        return exe_file

      if WINDOWS and '.' not in fname:
        if is_exe(exe_file + '.exe'):
          return exe_file + '.exe'
        if is_exe(exe_file + '.cmd'):
          return exe_file + '.cmd'
        if is_exe(exe_file + '.bat'):
          return exe_file + '.bat'

  return None


def vswhere(version):
  try:
    program_files = os.environ['ProgramFiles(x86)'] if 'ProgramFiles(x86)' in os.environ else os.environ['ProgramFiles']
    vswhere_path = os.path.join(program_files, 'Microsoft Visual Studio', 'Installer', 'vswhere.exe')
    output = json.loads(subprocess.check_output([vswhere_path, '-latest', '-version', '[%s.0,%s.0)' % (version, version + 1), '-requires', 'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath', '-format', 'json']))
    # Visual Studio 2017 Express is not included in the above search, and it does not have the VC.Tools.x86.x64 tool, so do a catch-all attempt as a fallback, to detect Express version.
    if len(output) == 0:
      output = json.loads(subprocess.check_output([vswhere_path, '-latest', '-version', '[%s.0,%s.0)' % (version, version + 1), '-products', '*', '-property', 'installationPath', '-format', 'json']))
    return str(output[0]['installationPath']) if len(output) > 0 else ''
  except Exception:
    return ''


def vs_filewhere(installation_path, platform, file):
  try:
    vcvarsall = os.path.join(installation_path, 'VC\\Auxiliary\\Build\\vcvarsall.bat')
    env = subprocess.check_output('cmd /c "%s" %s & where %s' % (vcvarsall, platform, file))
    paths = [path[:-len(file)] for path in env.split('\r\n') if path.endswith(file)]
    return paths[0]
  except Exception:
    return ''


CMAKE_GENERATOR = 'Unix Makefiles'
if WINDOWS:
  # Detect which CMake generator to use when building on Windows
  if '--mingw' in sys.argv:
    CMAKE_GENERATOR = 'MinGW Makefiles'
  elif '--vs2013' in sys.argv:
    CMAKE_GENERATOR = 'Visual Studio 12'
  elif '--vs2015' in sys.argv:
    CMAKE_GENERATOR = 'Visual Studio 14'
  elif '--vs2017' in sys.argv:
    CMAKE_GENERATOR = 'Visual Studio 15'
  else:
    program_files = os.environ['ProgramFiles(x86)'] if 'ProgramFiles(x86)' in os.environ else os.environ['ProgramFiles']
    vs2017_exists = len(vswhere(15)) > 0
    vs2015_exists = 'VS140COMNTOOLS' in os.environ or 'VSSDK140Install' in os.environ or os.path.isdir(os.path.join(program_files, 'Microsoft Visual Studio 14.0'))
    vs2013_exists = 'VS120COMNTOOLS' in os.environ or os.path.isdir(os.path.join(program_files, 'Microsoft Visual Studio 12.0'))
    mingw_exists = which('mingw32-make') is not None and which('g++') is not None
    if vs2015_exists:
      CMAKE_GENERATOR = 'Visual Studio 14'
    elif vs2017_exists:
      CMAKE_GENERATOR = 'Visual Studio 15' # VS2017 has an LLVM build issue, see https://github.com/kripken/emscripten-fastcomp/issues/185
    elif mingw_exists:
      CMAKE_GENERATOR = 'MinGW Makefiles'
    elif vs2013_exists:
      CMAKE_GENERATOR = 'Visual Studio 12' # VS2013 is no longer supported, so attempt it as a last resort if someone might want to insist using it.
    else:
      CMAKE_GENERATOR = '' # No detected generator


sys.argv = [a for a in sys.argv if a not in ('--mingw', '--vs2013', '--vs2015', '--vs2017')]


# Computes a suitable path prefix to use when building with a given generator.
def cmake_generator_prefix():
  if CMAKE_GENERATOR == 'Visual Studio 15':
    return '_vs2017'
  elif CMAKE_GENERATOR == 'Visual Studio 14':
    return '_vs2015'
  elif CMAKE_GENERATOR == 'MinGW Makefiles':
    return '_mingw'
  return '' # Unix Makefiles and Visual Studio 2013 do not specify a path prefix for backwards path compatibility


# Removes a directory tree even if it was readonly, and doesn't throw exception on failure.
def remove_tree(d):
  debug_print('remove_tree(' + str(d) + ')')
  try:
    def remove_readonly_and_try_again(func, path, exc_info):
      if not (os.stat(path).st_mode & stat.S_IWRITE):
        os.chmod(path, stat.S_IWRITE)
        func(path)
      else:
        raise
    shutil.rmtree(d, onerror=remove_readonly_and_try_again)
  except Exception as e:
    debug_print('remove_tree threw an exception, ignoring: ' + str(e))


def import_pywin32():
  if WINDOWS:
    try:
      import win32api
      import win32con
      return win32api, win32con
    except Exception:
      print('Failed to import Python Windows extensions win32api and win32con. Make sure you are using the version of python available in emsdk, or install PyWin extensions to the distribution of Python you are attempting to use. (This script was launched in python instance from "' + sys.executable + '")')
      sys.exit(1)


def win_set_environment_variable_direct(key, value, system=True):
  prev_path = os.environ['PATH']
  try:
    py = find_used_python()
    if py:
      py_path = to_native_path(py.expand_vars(py.activated_path))
      os.environ['PATH'] = os.environ['PATH'] + ';' + py_path
    win32api, win32con = import_pywin32()
    if system:
      # Read globally from ALL USERS section.
      folder = win32api.RegOpenKeyEx(win32con.HKEY_LOCAL_MACHINE, 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', 0, win32con.KEY_ALL_ACCESS)
    else:
      # Register locally from CURRENT USER section.
      folder = win32api.RegOpenKeyEx(win32con.HKEY_CURRENT_USER, 'Environment', 0, win32con.KEY_ALL_ACCESS)
    win32api.RegSetValueEx(folder, key, 0, win32con.REG_EXPAND_SZ, value)
    debug_print('Set key=' + key + ' with value ' + value + ' in registry.')
  except Exception as e:
    if e.args[0] == 5: # 'Access is denied.'
      print('Error! Failed to set the environment variable \'' + key + '\'! Setting environment variables permanently requires administrator access. Please rerun this command with administrative privileges. This can be done for example by holding down the Ctrl and Shift keys while opening a command prompt in start menu.')
      sys.exit(1)
    print('Failed to write environment variable ' + key + ':', file=sys.stderr)
    print(str(e), file=sys.stderr)
    win32api.RegCloseKey(folder)
    os.environ['PATH'] = prev_path
    return None

  win32api.RegCloseKey(folder)
  os.environ['PATH'] = prev_path
  win32api.PostMessage(win32con.HWND_BROADCAST, win32con.WM_SETTINGCHANGE, 0, 'Environment')


def win_get_environment_variable(key, system=True):
  prev_path = os.environ['PATH']
  try:
    py = find_used_python()
    if py:
      py_path = to_native_path(py.expand_vars(py.activated_path))
      os.environ['PATH'] = os.environ['PATH'] + ';' + py_path
    try:
      import win32api
      import win32con
      if system: # Read globally from ALL USERS section.
        folder = win32api.RegOpenKey(win32con.HKEY_LOCAL_MACHINE, 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment')
      else: # Register locally from CURRENT USER section.
        folder = win32api.RegOpenKey(win32con.HKEY_CURRENT_USER, 'Environment')
      value = str(win32api.RegQueryValueEx(folder, key)[0])
    except Exception:
      # PyWin32 is not available - read via os.environ. This has the drawback that expansion items such as %PROGRAMFILES% will have been expanded, so
      # need to be precise not to set these back to system registry, or expansion items would be lost.
      return os.environ[key]
  except Exception as e:
    if e.args[0] != 2: # 'The system cannot find the file specified.'
      print('Failed to read environment variable ' + key + ':', file=sys.stderr)
      print(str(e), file=sys.stderr)
    try:
      win32api.RegCloseKey(folder)
    except Exception:
      pass
    os.environ['PATH'] = prev_path
    return None
  win32api.RegCloseKey(folder)
  os.environ['PATH'] = prev_path
  return value


def win_environment_variable_exists(key, system=True):
  value = win_get_environment_variable(key, system)
  return value is not None and len(value) > 0


def win_get_active_environment_variable(key):
  value = win_get_environment_variable(key, False)
  if value is not None:
    return value
  return win_get_environment_variable(key, True)


def win_set_environment_variable(key, value, system=True):
  debug_print('set ' + str(key) + '=' + str(value) + ', in system=' + str(system), file=sys.stderr)
  previous_value = win_get_environment_variable(key, system)
  if previous_value == value:
    debug_print('  no need to set, since same value already exists.')
    return # No need to elevate UAC for nothing to set the same value, skip.

  if not value:
    try:
      if system:
        cmd = ['REG', 'DELETE', 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment', '/V', key, '/f']
      else:
        cmd = ['REG', 'DELETE', 'HKCU\\Environment', '/V', key, '/f']
      debug_print(str(cmd))
      value = subprocess.call(cmd, stdout=subprocess.PIPE)
    except Exception:
      return
    return

  try:
    if system:
      win_set_environment_variable_direct(key, value, system)
      return
    value = value.replace('%', '^%') # Escape % signs so that we don't expand references to environment variables.
    if len(value) >= 1024:
      print('ERROR! The new environment variable ' + key + ' is more than 1024 characters long! A value this long cannot be set via command line: please add the environment variable specified above to system environment manually via Control Panel.', file=sys.stderr)
      sys.exit(1)
    cmd = ['SETX', key, value]
    debug_print(str(cmd))
    retcode = subprocess.call(cmd, stdout=subprocess.PIPE)
    if retcode != 0:
      print('ERROR! Failed to set environment variable ' + key + '=' + value + '. You may need to set it manually.', file=sys.stderr)
  except Exception as e:
    print('ERROR! Failed to set environment variable ' + key + '=' + value + ':', file=sys.stderr)
    print(str(e), file=sys.stderr)
    print('You may need to set it manually.', file=sys.stderr)


def win_delete_environment_variable(key, system=True):
  debug_print('win_delete_environment_variable(key=' + key + ', system=' + str(system) + ')')
  win_set_environment_variable(key, None, system)


# Returns the absolute pathname to the given path inside the Emscripten SDK.
def sdk_path(path):
  if os.path.isabs(path):
    return path
  else:
    return to_unix_path(os.path.join(os.path.dirname(os.path.realpath(__file__)), path))


# Modifies the given file in-place to contain '\r\n' line endings.
def file_to_crlf(filename):
  text = open(filename, 'r').read()
  text = text.replace('\r\n', '\n').replace('\n', '\r\n')
  open(filename, 'wb').write(text)


# Modifies the given file in-place to contain '\n' line endings.
def file_to_lf(filename):
  text = open(filename, 'r').read()
  text = text.replace('\r\n', '\n')
  open(filename, 'wb').write(text)


# Removes a single file, suppressing exceptions on failure.
def rmfile(filename):
  debug_print('rmfile(' + filename + ')')
  try:
    os.remove(filename)
  except:
    pass


def fix_lineendings(filename):
  if WINDOWS:
    file_to_crlf(filename)
  else:
    file_to_lf(filename)


# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def mkdir_p(path):
  debug_print('mkdir_p(' + path + ')')
  if os.path.exists(path):
    return
  try:
    os.makedirs(path)
  except OSError as exc: # Python >2.5
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      pass
    else:
      raise


def num_files_in_directory(path):
  if not os.path.isdir(path):
    return 0
  return len([name for name in os.listdir(path) if os.path.exists(os.path.join(path, name))])


def run(cmd, cwd=None):
  debug_print('run(cmd=' + str(cmd) + ', cwd=' + str(cwd) + ')')
  process = subprocess.Popen(cmd, cwd=cwd, env=os.environ.copy())
  process.communicate()
  if process.returncode != 0:
    print(str(cmd) + ' failed with error code ' + str(process.returncode) + '!')
  return process.returncode


# http://pythonicprose.blogspot.fi/2009/10/python-extract-targz-archive.html
def untargz(source_filename, dest_dir, unpack_even_if_exists=False):
  debug_print('untargz(source_filename=' + source_filename + ', dest_dir=' + dest_dir + ')')
  if not unpack_even_if_exists and num_files_in_directory(dest_dir) > 0:
    print("File '" + source_filename + "' has already been unpacked, skipping.")
    return True
  print("Unpacking '" + source_filename + "' to '" + dest_dir + "'")
  mkdir_p(dest_dir)
  run(['tar', '-xvf' if VERBOSE else '-xf', sdk_path(source_filename), '--strip', '1'], cwd=dest_dir)
  # tfile = tarfile.open(source_filename, 'r:gz')
  # tfile.extractall(dest_dir)
  return True


# On Windows, it is not possible to reference path names that are longer than ~260 characters, unless the path is referenced via a "\\?\" prefix.
# See https://msdn.microsoft.com/en-us/library/aa365247.aspx#maxpath and http://stackoverflow.com/questions/3555527/python-win32-filename-length-workaround
# In that mode, forward slashes cannot be used as delimiters.
def fix_potentially_long_windows_pathname(pathname):
  if not WINDOWS:
    return pathname
  # Test if emsdk calls fix_potentially_long_windows_pathname() with long relative paths (which is problematic)
  if not os.path.isabs(pathname) and len(pathname) > 200:
    print('Warning: Seeing a relative path "' + pathname + '" which is dangerously long for being referenced as a short Windows path name. Refactor emsdk to be able to handle this!')
  if pathname.startswith('\\\\?\\'):
    return pathname
  return '\\\\?\\' + os.path.normpath(pathname.replace('/', '\\'))


# On windows, rename/move will fail if the destination exists, and there is no
# race-free way to do it. This method removes the destination if it exists, so
# the move always works
def move_with_overwrite(src, dest):
  if os.path.exists(dest):
    os.remove(dest)
  os.rename(src, dest)


# http://stackoverflow.com/questions/12886768/simple-way-to-unzip-file-in-python-on-all-oses
def unzip(source_filename, dest_dir, unpack_even_if_exists=False):
  debug_print('unzip(source_filename=' + source_filename + ', dest_dir=' + dest_dir + ')')
  if not unpack_even_if_exists and num_files_in_directory(dest_dir) > 0:
    print("File '" + source_filename + "' has already been unpacked, skipping.")
    return True
  print("Unpacking '" + source_filename + "' to '" + dest_dir + "'")
  mkdir_p(dest_dir)
  common_subdir = None
  try:
    with zipfile.ZipFile(source_filename) as zf:
      # Implement '--strip 1' behavior to unzipping by testing if all the files in the zip reside in a common subdirectory, and if so,
      # we move the output tree at the end of uncompression step.
      for member in zf.infolist():
        words = member.filename.split('/')
        if len(words) > 1:  # If there is a directory component?
          if common_subdir is None:
            common_subdir = words[0]
          elif common_subdir != words[0]:
            common_subdir = None
            break
        else:
          common_subdir = None
          break

      unzip_to_dir = dest_dir
      if common_subdir:
        unzip_to_dir = os.path.join('/'.join(dest_dir.split('/')[:-1]), 'unzip_temp')

      # Now do the actual decompress.
      for member in zf.infolist():
        zf.extract(member, fix_potentially_long_windows_pathname(unzip_to_dir))
        dst_filename = os.path.join(unzip_to_dir, member.filename)

        # See: https://stackoverflow.com/questions/42326428/zipfile-in-python-file-permission
        unix_attributes = member.external_attr >> 16
        if unix_attributes:
          os.chmod(dst_filename, unix_attributes)

        # Move the extracted file to its final location without the base directory name, if we are stripping that away.
        if common_subdir:
          if not member.filename.startswith(common_subdir):
            raise Exception('Unexpected filename "' + member.filename + '"!')
          stripped_filename = '.' + member.filename[len(common_subdir):]
          final_dst_filename = os.path.join(dest_dir, stripped_filename)
          if stripped_filename.endswith('/'): # Directory?
            d = fix_potentially_long_windows_pathname(final_dst_filename)
            if not os.path.isdir(d):
              os.mkdir(d)
          else:
            parent_dir = os.path.dirname(fix_potentially_long_windows_pathname(final_dst_filename))
            if parent_dir and not os.path.exists(parent_dir):
              os.makedirs(parent_dir)
            move_with_overwrite(fix_potentially_long_windows_pathname(dst_filename), fix_potentially_long_windows_pathname(final_dst_filename))

      if common_subdir:
        try:
          remove_tree(unzip_to_dir)
        except:
          pass
  except zipfile.BadZipfile as e:
    print("Unzipping file '" + source_filename + "' failed due to reason: " + str(e) + "! Removing the corrupted zip file.")
    rmfile(source_filename)
    return False
  except Exception as e:
    print("Unzipping file '" + source_filename + "' failed due to reason: " + str(e))
    return False

  return True


# This function interprets whether the given string looks like a path to a directory instead of a file, without looking at the actual filesystem.
# 'a/b/c' points to directory, so does 'a/b/c/', but 'a/b/c.x' is parsed as a filename
def path_points_to_directory(path):
  if path == '.':
     return True
  last_slash = max(path.rfind('/'), path.rfind('\\'))
  last_dot = path.rfind('.')
  no_suffix = last_dot < last_slash or last_dot == -1
  if no_suffix:
    return True
  suffix = path[last_dot:]
  # Very simple logic for the only file suffixes used by emsdk downloader. Other
  # suffixes, like 'clang-3.2' are treated as dirs.
  if suffix in ('.exe', '.zip', '.txt'):
    return False
  else:
    return True


def get_content_length(download):
  try:
    meta = download.info()
    if hasattr(meta, "getheaders") and hasattr(meta.getheaders, "Content-Length"):
      return int(meta.getheaders("Content-Length")[0])
    elif hasattr(download, "getheader") and download.getheader('Content-Length'):
      return int(download.getheader('Content-Length'))
    elif hasattr(meta, "getheader") and meta.getheader('Content-Length'):
      return int(meta.getheader('Content-Length'))
  except Exception:
    pass

  return 0


def get_download_target(url, dstpath, filename_prefix=''):
  file_name = filename_prefix + url.split('/')[-1]
  if path_points_to_directory(dstpath):
    file_name = os.path.join(dstpath, file_name)
  else:
    file_name = dstpath

  # Treat all relative destination paths as relative to the SDK root directory, not the current working directory.
  file_name = sdk_path(file_name)

  return file_name


# On success, returns the filename on the disk pointing to the destination file that was produced
# On failure, returns None.
def download_file(url, dstpath, download_even_if_exists=False, filename_prefix=''):
  debug_print('download_file(url=' + url + ', dstpath=' + dstpath + ')')
  file_name = get_download_target(url, dstpath, filename_prefix)

  if os.path.exists(file_name) and not download_even_if_exists:
    print("File '" + file_name + "' already downloaded, skipping.")
    return file_name
  try:
    u = urlopen(url)
    mkdir_p(os.path.dirname(file_name))
    with open(file_name, 'wb') as f:
      file_size = get_content_length(u)
      if file_size > 0:
        print("Downloading: %s from %s, %s Bytes" % (file_name, url, file_size))
      else:
        print("Downloading: %s from %s" % (file_name, url))

      file_size_dl = 0
      # Draw a progress bar 80 chars wide (in non-TTY mode)
      progress_max = 80 - 4
      progress_shown = 0
      block_sz = 8192
      if not TTY_OUTPUT:
          print(' [', end='')
      while True:
          buffer = u.read(block_sz)
          if not buffer:
              break

          file_size_dl += len(buffer)
          f.write(buffer)
          if file_size:
              percent = file_size_dl * 100.0 / file_size
              if TTY_OUTPUT:
                  status = r" %10d  [%3.02f%%]" % (file_size_dl, percent)
                  print(status, end='\r')
              else:
                  while progress_shown < progress_max * percent / 100:
                      print('-', end='')
                      sys.stdout.flush()
                      progress_shown += 1
      if not TTY_OUTPUT:
        print(']')
        sys.stdout.flush()
  except Exception as e:
    print("Error downloading URL '" + url + "': " + str(e))
    rmfile(file_name)
    return None
  except KeyboardInterrupt:
    print("Aborted by User, exiting")
    rmfile(file_name)
    sys.exit(1)
  return file_name


def run_get_output(cmd, cwd=None):
  debug_print('run_get_output(cmd=' + str(cmd) + ', cwd=' + str(cwd) + ')')
  process = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, env=os.environ.copy(), universal_newlines=True)
  stdout, stderr = process.communicate()
  return (process.returncode, stdout, stderr)


# must_succeed: If false, the search is performed silently without printing out errors if not found. Empty string is returned if git is not found.
#               If true, the search is required to succeed, and the execution will terminate with sys.exit(1) if not found.
def GIT(must_succeed=True):
  # The order in the following is important, and specifies the preferred order of using the git tools.
  # Primarily use git from emsdk if installed. If not, use system git.
  gits = ['git/1.9.4/bin/git.exe', which('git')]
  for git in gits:
    try:
      ret, stdout, stderr = run_get_output([git, '--version'])
      if ret == 0:
        return git
    except:
      pass
  if must_succeed:
    if WINDOWS:
      print("ERROR: git executable was not found. Please install it by typing 'emsdk install git-1.9.4', or alternatively by installing it manually from http://git-scm.com/downloads . If you install git manually, remember to add it to PATH")
    elif OSX:
      print("ERROR: git executable was not found. Please install git for this operation! This can be done from http://git-scm.com/ , or by installing XCode and then the XCode Command Line Tools (see http://stackoverflow.com/questions/9329243/xcode-4-4-command-line-tools )")
    elif LINUX:
      print("ERROR: git executable was not found. Please install git for this operation! This can be probably be done using your package manager, see http://git-scm.com/book/en/Getting-Started-Installing-Git")
    else:
      print("ERROR: git executable was not found. Please install git for this operation!")
    sys.exit(1)
  return '' # Not found


def git_repo_version(repo_path):
  returncode, stdout, stderr = run_get_output([GIT(), 'log', '-n', '1', '--pretty="%aD %H"'], cwd=repo_path)
  if returncode == 0:
    return stdout.strip()
  else:
    return ""


def git_recent_commits(repo_path, n=20):
  returncode, stdout, stderr = run_get_output([GIT(), 'log', '-n', str(n), '--pretty="%H"'], cwd=repo_path)
  if returncode == 0:
    return stdout.strip().replace('\r', '').replace('"', '').split('\n')
  else:
    return []


def git_clone(url, dstpath):
  debug_print('git_clone(url=' + url + ', dstpath=' + dstpath + ')')
  if os.path.isdir(os.path.join(dstpath, '.git')):
    print("Repository '" + url + "' already cloned to directory '" + dstpath + "', skipping.")
    return True
  mkdir_p(dstpath)
  git_clone_args = []
  if GIT_CLONE_SHALLOW:
    git_clone_args += ['--depth', '1']
  return run([GIT(), 'clone'] + git_clone_args + [url, dstpath]) == 0


def git_checkout_and_pull(repo_path, branch):
  debug_print('git_checkout_and_pull(repo_path=' + repo_path + ', branch=' + branch + ')')
  ret = run([GIT(), 'fetch', 'origin'], repo_path)
  if ret != 0:
    return False
  try:
    print("Fetching latest changes to the branch '" + branch + "' for '" + repo_path + "'...")
    ret = run([GIT(), 'fetch', 'origin'], repo_path)
    if ret != 0:
      return False
#  run([GIT, 'checkout', '-b', branch, '--track', 'origin/'+branch], repo_path)
    ret = run([GIT(), 'checkout', '--quiet', branch], repo_path) # this line assumes that the user has not gone and manually messed with the repo and added new remotes to ambiguate the checkout.
    if ret != 0:
      return False
    ret = run([GIT(), 'merge', '--ff-only', 'origin/' + branch], repo_path) # this line assumes that the user has not gone and made local changes to the repo
    if ret != 0:
      return False
  except:
    print('git operation failed!')
    return False
  print("Successfully updated and checked out branch '" + branch + "' on repository '" + repo_path + "'")
  print("Current repository version: " + git_repo_version(repo_path))
  return True


def git_clone_checkout_and_pull(url, dstpath, branch):
  debug_print('git_clone_checkout_and_pull(url=' + url + ', dstpath=' + dstpath + ', branch=' + branch + ')')
  success = git_clone(url, dstpath)
  if not success:
    return False
  success = git_checkout_and_pull(dstpath, branch)
  return success


# Each tool can have its own build type, or it can be overridden on the command line.
def decide_cmake_build_type(tool):
  global CMAKE_BUILD_TYPE_OVERRIDE
  if CMAKE_BUILD_TYPE_OVERRIDE:
    return CMAKE_BUILD_TYPE_OVERRIDE
  else:
    return tool.cmake_build_type


# The root directory of the build.
def fastcomp_build_dir(tool):
  generator_suffix = ''
  if CMAKE_GENERATOR == 'Visual Studio 10':
    generator_suffix = '_vs2010'
  elif CMAKE_GENERATOR == 'Visual Studio 11':
    generator_suffix = '_vs2012'
  elif CMAKE_GENERATOR == 'Visual Studio 12':
    generator_suffix = '_vs2013'
  elif CMAKE_GENERATOR == 'Visual Studio 14':
    generator_suffix = '_vs2015'
  elif CMAKE_GENERATOR == 'Visual Studio 15':
    generator_suffix = '_vs2017'
  elif CMAKE_GENERATOR == 'MinGW Makefiles':
    generator_suffix = '_mingw'

  bitness_suffix = '_32' if tool.bitness == 32 else '_64'

  if hasattr(tool, 'git_branch'):
    build_dir = 'build_' + tool.git_branch.replace(os.sep, '-') + generator_suffix + bitness_suffix
  else:
    build_dir = 'build_' + tool.version + generator_suffix + bitness_suffix
  return build_dir


def exe_suffix(filename):
  if WINDOWS and not filename.endswith('.exe'):
    filename += '.exe'
  return filename


# The directory where the binaries are produced. (relative to the installation root directory of the tool)
def fastcomp_build_bin_dir(tool):
  build_dir = fastcomp_build_dir(tool)
  if WINDOWS and 'Visual Studio' in CMAKE_GENERATOR:
    old_llvm_bin_dir = os.path.join(build_dir, 'bin', decide_cmake_build_type(tool))

    new_llvm_bin_dir = None
    default_cmake_build_type = decide_cmake_build_type(tool)
    cmake_build_types = [default_cmake_build_type, 'Release', 'RelWithDebInfo', 'MinSizeRel', 'Debug']
    for build_type in cmake_build_types:
      d = os.path.join(build_dir, build_type, 'bin')
      if os.path.isfile(os.path.join(tool.installation_path(), d, exe_suffix('clang'))):
        new_llvm_bin_dir = d
        break

    if new_llvm_bin_dir and os.path.exists(os.path.join(tool.installation_path(), new_llvm_bin_dir)):
      return new_llvm_bin_dir
    elif os.path.exists(os.path.join(tool.installation_path(), old_llvm_bin_dir)):
      return old_llvm_bin_dir
    return os.path.join(build_dir, default_cmake_build_type, 'bin')
  else:
    return os.path.join(build_dir, 'bin')


def build_env(generator):
  build_env = os.environ.copy()

  # To work around a build issue with older Mac OS X builds, add -stdlib=libc++ to all builds.
  # See https://groups.google.com/forum/#!topic/emscripten-discuss/5Or6QIzkqf0
  if OSX:
    build_env['CXXFLAGS'] = ((build_env['CXXFLAGS'] + ' ') if hasattr(build_env, 'CXXFLAGS') else '') + '-stdlib=libc++'
  elif 'Visual Studio 15' in generator:
    path = vswhere(15)
    build_env['VCTargetsPath'] = os.path.join(path, 'Common7\\IDE\\VC\\VCTargets')

    # CMake and VS2017 cl.exe needs to have mspdb140.dll et al. in its PATH.
    vc_bin_paths = [vs_filewhere(path, 'amd64', 'cl.exe'),
                    vs_filewhere(path, 'x86', 'cl.exe')]
    for path in vc_bin_paths:
      if os.path.isdir(path):
          build_env['PATH'] = build_env['PATH'] + ';' + path

  elif 'Visual Studio 14' in generator or 'Visual Studio 2015' in generator:
    build_env['VCTargetsPath'] = os.path.join(os.environ['ProgramFiles(x86)'], 'MSBuild/Microsoft.Cpp/v4.0/V140')

    # CMake and VS2015 cl.exe needs to have mspdb140.dll et al. in its PATH.
    vc_bin_paths = [os.path.join(os.environ['ProgramFiles'], 'Microsoft Visual Studio 14.0\\VC\\bin'),
                    os.path.join(os.environ['ProgramFiles(x86)'], 'Microsoft Visual Studio 14.0\\VC\\bin')]
    for path in vc_bin_paths:
      if os.path.isdir(path):
        build_env['PATH'] = build_env['PATH'] + ';' + path

  elif 'Visual Studio 12' in generator or 'Visual Studio 2013' in generator:
    build_env['VCTargetsPath'] = os.path.join(os.environ['ProgramFiles(x86)'], 'MSBuild/Microsoft.Cpp/v4.0/V120')

  return build_env


def get_generator_for_sln_file(sln_file):
  contents = open(sln_file, 'r').read()
  if '# Visual Studio 15' in contents:
    return 'Visual Studio 15'
  if '# Visual Studio Express 2015' in contents or '# Visual Studio 2015' in contents or '# Visual Studio 14' in contents:
    return 'Visual Studio 14'
  if '# Visual Studio Express 2013' in contents or '# Visual Studio 2013' in contents or '# Visual Studio 12' in contents:
    return 'Visual Studio 12'
  raise Exception('Unknown generator used to build solution file ' + sln_file)


def find_msbuild(sln_file):
  # The following logic attempts to find a Visual Studio version specific MSBuild.exe from a list of known locations. This logic
  # exists because it was detected that when multiple Visual Studio versions exist (VS2013 & VS2015), their MSBuild.exes might not
  # be able to drive a build proper. This search is messy, and perhaps in VS >= 2017 or similar none of this logic would be needed.
  # Ideally would be able to do "cmake --build path/to/cmake/build/directory --config Debug|RelWithDebInfo|MinSizeRel|Release" across
  # all platforms, but around VS2013 era this did not work. This could be reattempted when support for VS 2015 is dropped.
  search_paths_vs2015 = [os.path.join(os.environ['ProgramFiles'], 'MSBuild/14.0/Bin/amd64'),
                         os.path.join(os.environ['ProgramFiles(x86)'], 'MSBuild/14.0/Bin/amd64'),
                         os.path.join(os.environ['ProgramFiles'], 'MSBuild/14.0/Bin'),
                         os.path.join(os.environ['ProgramFiles(x86)'], 'MSBuild/14.0/Bin')]
  search_paths_vs2013 = [os.path.join(os.environ['ProgramFiles'], 'MSBuild/12.0/Bin/amd64'),
                         os.path.join(os.environ['ProgramFiles(x86)'], 'MSBuild/12.0/Bin/amd64'),
                         os.path.join(os.environ['ProgramFiles'], 'MSBuild/12.0/Bin'),
                         os.path.join(os.environ['ProgramFiles(x86)'], 'MSBuild/12.0/Bin')]
  search_paths_old = [os.path.join(os.environ["WINDIR"], 'Microsoft.NET/Framework/v4.0.30319')]
  generator = get_generator_for_sln_file(sln_file)
  debug_print('find_msbuild looking for generator ' + str(generator))
  if generator == 'Visual Studio 15':
    path = vswhere(15)
    search_paths = [os.path.join(path, 'MSBuild/15.0/Bin/amd64'),
                    os.path.join(path, 'MSBuild/15.0/Bin')]
  elif generator == 'Visual Studio 14':
    search_paths = search_paths_vs2015
  elif generator == 'Visual Studio 12':
    search_paths = search_paths_vs2013 + search_paths_old
  else:
    raise Exception('Unknown generator!')

  for path in search_paths:
    p = os.path.join(path, 'MSBuild.exe')
    debug_print('Searching for MSBuild.exe: ' + p)
    if os.path.isfile(p):
      return p
  debug_print('MSBuild.exe in PATH? ' + str(which('MSBuild.exe')))
  return which('MSBuild.exe') # Last fallback, try any MSBuild from PATH (might not be compatible, but best effort)


def make_build(build_root, build_type, build_target_platform='x64'):
  debug_print('make_build(build_root=' + build_root + ', build_type=' + build_type + ', build_target_platform=' + build_target_platform + ')')
  global CPU_CORES
  if CPU_CORES > 1:
    print('Performing a parallel build with ' + str(CPU_CORES) + ' cores.')
  else:
    print('Performing a singlethreaded build.')

  generator_to_use = CMAKE_GENERATOR

  if WINDOWS:
    if 'Visual Studio' in CMAKE_GENERATOR:
      solution_name = str(subprocess.check_output(['dir', '/b', '*.sln'], shell=True, cwd=build_root).decode('utf-8').strip())
      generator_to_use = get_generator_for_sln_file(os.path.join(build_root, solution_name))
      # Disabled for now: Don't pass /maxcpucount argument to msbuild, since it looks like when building, msbuild already automatically spawns the full amount of logical
      # cores the system has, and passing the number of logical cores here has been observed to give a quadratic N*N explosion on the number of spawned processes
      # (e.g. on a Core i7 5960X with 16 logical cores, it would spawn 16*16=256 cl.exe processes, which would start crashing when running out of system memory)
      #      make = [find_msbuild(os.path.join(build_root, solution_name)), '/maxcpucount:' + str(CPU_CORES), '/t:Build', '/p:Configuration=' + build_type, '/nologo', '/verbosity:minimal', solution_name]
      make = [find_msbuild(os.path.join(build_root, solution_name)), '/t:Build', '/p:Configuration=' + build_type, '/p:Platform=' + build_target_platform, '/nologo', '/verbosity:minimal', solution_name]
    else:
      make = ['mingw32-make', '-j' + str(CPU_CORES)]
  else:
    make = ['cmake', '--build', '.', '--', '-j' + str(CPU_CORES)]

  # Build
  try:
    print('Running build: ' + str(make))
    ret = subprocess.check_call(make, cwd=build_root, env=build_env(generator_to_use))
    if ret != 0:
      print('Build failed with exit code ' + ret + '!', file=sys.stderr)
      print('Working directory: ' + build_root, file=sys.stderr)
      return False
  except Exception as e:
    print('Build failed due to exception!', file=sys.stderr)
    print('Working directory: ' + build_root, file=sys.stderr)
    print(str(e), file=sys.stderr)
    return False

  return True


def cmake_configure(generator, build_root, src_root, build_type, extra_cmake_args=[]):
  debug_print('cmake_configure(generator=' + str(generator) + ', build_root=' + str(build_root) + ', src_root=' + str(src_root) + ', build_type=' + str(build_type) + ', extra_cmake_args=' + str(extra_cmake_args) + ')')
  # Configure
  if not os.path.isdir(build_root):
    os.mkdir(build_root) # Create build output directory if it doesn't yet exist.
  try:
    if generator:
      generator = ['-G', generator]
    else:
      generator = []
    cmdline = ['cmake'] + generator + ['-DCMAKE_BUILD_TYPE=' + build_type, '-DPYTHON_EXECUTABLE=' + sys.executable] + extra_cmake_args + [src_root]
    print('Running CMake: ' + str(cmdline))

    def quote_parens(x):
      if ' ' in x:
        return '"' + x.replace('"', '\\"') + '"'
      else:
        return x

    open(os.path.join(build_root, 'recmake.' + ('bat' if WINDOWS else 'sh')), 'w').write(' '.join(map(quote_parens, cmdline))) # Create a file 'recmake.bat/sh' in the build root that user can call to manually recmake the build tree with the previous build params
    ret = subprocess.check_call(cmdline, cwd=build_root, env=build_env(CMAKE_GENERATOR))
    if ret != 0:
      print('CMake invocation failed with exit code ' + ret + '!', file=sys.stderr)
      print('Working directory: ' + build_root, file=sys.stderr)
      return False
  except OSError as e:
    if e.errno == errno.ENOENT:
      print(str(e), file=sys.stderr)
      print('Could not run CMake, perhaps it has not been installed?', file=sys.stderr)
      if WINDOWS:
        print('Installing this package requires CMake. Get it from http://www.cmake.org/', file=sys.stderr)
      elif LINUX:
        print('Installing this package requires CMake. Get it via your system package manager (e.g. sudo apt-get install cmake), or from http://www.cmake.org/', file=sys.stderr)
      elif OSX:
        print('Installing this package requires CMake. Get it via a OSX package manager (Homebrew: "brew install cmake", or MacPorts: "sudo port install cmake"), or from http://www.cmake.org/', file=sys.stderr)
      return False
    raise
  except Exception as e:
    print('CMake invocation failed due to exception!', file=sys.stderr)
    print('Working directory: ' + build_root, file=sys.stderr)
    print(str(e), file=sys.stderr)
    return False

  return True


def xcode_sdk_version():
  try:
    output = subprocess.check_output(['xcrun', '--show-sdk-version'])
    if sys.version_info >= (3,):
      output = output.decode('utf8')
    return output.strip().split('.')
  except:
    return subprocess.checkplatform.mac_ver()[0].split('.')


def build_llvm_tool(tool):
  debug_print('build_llvm_tool(' + str(tool) + ')')
  fastcomp_root = tool.installation_path()
  fastcomp_src_root = os.path.join(fastcomp_root, 'src')
  if hasattr(tool, 'git_branch'):  # Does this tool want to be git cloned from github?
    success = git_clone_checkout_and_pull(tool.download_url(), fastcomp_src_root, tool.git_branch)
    if not success:
      return False
    clang_root = os.path.join(fastcomp_src_root, 'tools/clang')
    success = git_clone_checkout_and_pull(tool.clang_url, clang_root, tool.git_branch)
    if not success:
      return False
    if hasattr(tool, 'lld_url'):
      lld_root = os.path.join(fastcomp_src_root, 'tools/lld')
      success = git_clone_checkout_and_pull(tool.lld_url, lld_root, tool.git_branch)
      if not success:
        return False
  else: # Not a git cloned tool, so instead download from git tagged releases
    success = download_and_unzip(tool.download_url(), fastcomp_src_root, filename_prefix='llvm-e')
    if not success:
      return False
    success = download_and_unzip(tool.windows_clang_url if WINDOWS else tool.unix_clang_url, os.path.join(fastcomp_src_root, 'tools/clang'), filename_prefix='clang-e')
    if not success:
      return False

  cmake_generator = CMAKE_GENERATOR
  if 'Visual Studio' in CMAKE_GENERATOR and tool.bitness == 64:
    cmake_generator += ' Win64'

  build_dir = fastcomp_build_dir(tool)
  build_root = os.path.join(fastcomp_root, build_dir)

  build_type = decide_cmake_build_type(tool)

  # Configure
  global BUILD_FOR_TESTING, ENABLE_LLVM_ASSERTIONS
  tests_arg = 'ON' if BUILD_FOR_TESTING else 'OFF'

  enable_assertions = ENABLE_LLVM_ASSERTIONS.lower() == 'on' or (ENABLE_LLVM_ASSERTIONS == 'auto' and build_type.lower() != 'release' and build_type.lower() != 'minsizerel')

  only_supports_wasm = hasattr(tool, 'only_supports_wasm')
  if ARCH == 'x86' or ARCH == 'x86_64':
    targets_to_build = 'X86'
  elif ARCH == 'arm':
    targets_to_build = 'ARM'
  elif ARCH == 'aarch64':
    targets_to_build = 'AArch64'
  else:
    # May have problems with emconfigure
    targets_to_build = ''
  if not only_supports_wasm:
    if targets_to_build != '':
      targets_to_build += ';'
    targets_to_build += 'JSBackend'
  args = ['-DLLVM_TARGETS_TO_BUILD=' + targets_to_build, '-DLLVM_INCLUDE_EXAMPLES=OFF', '-DCLANG_INCLUDE_EXAMPLES=OFF', '-DLLVM_INCLUDE_TESTS=' + tests_arg, '-DCLANG_INCLUDE_TESTS=' + tests_arg, '-DLLVM_ENABLE_ASSERTIONS=' + ('ON' if enable_assertions else 'OFF')]
  if os.environ.get('LLVM_CMAKE_ARGS'):
    extra_args = os.environ['LLVM_CMAKE_ARGS'].split(',')
    print('Passing the following extra arguments to LLVM CMake configuration: ' + str(extra_args))
    args += extra_args

  # MacOS < 10.13 workaround for LLVM build bug https://github.com/kripken/emscripten/issues/5418:
  # specify HAVE_FUTIMENS=0 in the build if building with target SDK that is older than 10.13.
  if OSX and (not os.environ.get('LLVM_CMAKE_ARGS') or 'HAVE_FUTIMENS' not in os.environ.get('LLVM_CMAKE_ARGS')) and xcode_sdk_version() < ['10', '13']:
    print('Passing -DHAVE_FUTIMENS=0 to LLVM CMake configure to workaround https://github.com/kripken/emscripten/issues/5418. Please update to macOS 10.13 or newer')
    args += ['-DHAVE_FUTIMENS=0']

  success = cmake_configure(cmake_generator, build_root, fastcomp_src_root, build_type, args)
  if not success:
    return False

  # Make
  success = make_build(build_root, build_type, 'x64' if tool.bitness == 64 else 'Win32')
  return success


# Emscripten asm.js optimizer build scripts:
def optimizer_build_root(tool):
  build_root = tool.installation_path().strip()
  if build_root.endswith('/') or build_root.endswith('\\'):
    build_root = build_root[:-1]
  generator_prefix = cmake_generator_prefix()
  build_root = build_root + generator_prefix + '_' + str(tool.bitness) + 'bit_optimizer'
  return build_root


def uninstall_optimizer(tool):
  debug_print('uninstall_optimizer(' + str(tool) + ')')
  build_root = optimizer_build_root(tool)
  print("Deleting path '" + build_root + "'")
  try:
    remove_tree(build_root)
    os.remove(build_root)
  except:
    pass


def is_optimizer_installed(tool):
  build_root = optimizer_build_root(tool)
  return os.path.exists(build_root)


def build_optimizer_tool(tool):
  debug_print('build_optimizer_tool(' + str(tool) + ')')
  src_root = os.path.join(tool.installation_path(), 'tools', 'optimizer')
  build_root = optimizer_build_root(tool)
  build_type = decide_cmake_build_type(tool)

  # Configure
  cmake_generator = CMAKE_GENERATOR
  if 'Visual Studio' in CMAKE_GENERATOR and tool.bitness == 64:
    cmake_generator += ' Win64'
  success = cmake_configure(cmake_generator, build_root, src_root, build_type)
  if not success:
    return False

  # Make
  success = make_build(build_root, build_type, 'x64' if tool.bitness == 64 else 'Win32')
  return success


# Binaryen build scripts:
def binaryen_build_root(tool):
  build_root = tool.installation_path().strip()
  if build_root.endswith('/') or build_root.endswith('\\'):
    build_root = build_root[:-1]
  generator_prefix = cmake_generator_prefix()
  build_root = build_root + generator_prefix + '_' + str(tool.bitness) + 'bit_binaryen'
  return build_root


def uninstall_binaryen(tool):
  debug_print('uninstall_binaryen(' + str(tool) + ')')
  build_root = binaryen_build_root(tool)
  print("Deleting path '" + build_root + "'")
  try:
    remove_tree(build_root)
    os.remove(build_root)
  except:
    pass


def is_binaryen_installed(tool):
  build_root = binaryen_build_root(tool)
  return os.path.exists(build_root)


def build_binaryen_tool(tool):
  debug_print('build_binaryen_tool(' + str(tool) + ')')
  src_root = tool.installation_path()
  build_root = binaryen_build_root(tool)
  build_type = decide_cmake_build_type(tool)

  # Configure
  args = []

  cmake_generator = CMAKE_GENERATOR
  if 'Visual Studio' in CMAKE_GENERATOR:
    if tool.bitness == 64:
      cmake_generator += ' Win64'
    if BUILD_FOR_TESTING:
      args += ['-DRUN_STATIC_ANALYZER=1']

  success = cmake_configure(cmake_generator, build_root, src_root, build_type, args)
  if not success:
    return False

  # Make
  success = make_build(build_root, build_type, 'x64' if tool.bitness == 64 else 'Win32')

  # Deploy scripts needed from source repository to build directory
  remove_tree(os.path.join(build_root, 'scripts'))
  shutil.copytree(os.path.join(src_root, 'scripts'), os.path.join(build_root, 'scripts'))
  remove_tree(os.path.join(build_root, 'src', 'js'))
  shutil.copytree(os.path.join(src_root, 'src', 'js'), os.path.join(build_root, 'src', 'js'))

  return success


def download_and_unzip(zipfile, dest_dir, download_even_if_exists=False, filename_prefix=''):
  debug_print('download_and_unzip(zipfile=' + zipfile + ', dest_dir=' + dest_dir + ')')

  url = urljoin(emsdk_packages_url, zipfile)
  download_target = get_download_target(url, zips_subdir, filename_prefix)

  # If the archive was already downloaded, and the directory it would be
  # unpacked to has contents, assume it's the same contents and skip.
  if not download_even_if_exists and os.path.exists(download_target) and num_files_in_directory(dest_dir) > 0:
    print("The contents of file '" + zipfile + "' already exist in destination '" + dest_dir + "', skipping.")
    return True
  # Otherwise, if the archive must be downloaded, always write into the
  # target directory, since it may be a new version of a tool that gets
  # installed to the same place (that is, a different download name
  # indicates different contents).
  download_even_if_exists = True

  received_download_target = download_file(url, zips_subdir, download_even_if_exists, filename_prefix)
  if not received_download_target:
    return False
  assert received_download_target == download_target
  if zipfile.endswith('.zip'):
    return unzip(download_target, dest_dir, unpack_even_if_exists=download_even_if_exists)
  else:
    return untargz(download_target, dest_dir, unpack_even_if_exists=download_even_if_exists)


def to_native_path(p):
  if WINDOWS and not MSYS:
    return to_unix_path(p).replace('/', '\\')
  else:
    return to_unix_path(p)


# Finds and returns a list of the directories that need to be added to PATH for the given set of tools.
def get_required_path(active_tools):
  path_add = [to_native_path(emsdk_path())]
  for tool in active_tools:
    if hasattr(tool, 'activated_path'):
      path_add += [to_native_path(tool.expand_vars(tool.activated_path))]
  return path_add


# Returns the absolute path to the file '.emscripten' for the current user on this system.
def dot_emscripten_path():
  return os.path.join(emscripten_config_directory, ".emscripten")


dot_emscripten = {}


def parse_key_value(line):
  if not line:
    return ('', '')
  eq = line.find('=')
  if eq != -1:
    key = line[0:eq].strip()
    value = line[eq + 1:].strip()
    return (key, value)
  else:
    return (key, '')


def load_dot_emscripten():
  global dot_emscripten
  dot_emscripten = {}
  lines = []
  try:
    lines = open(dot_emscripten_path(), "r").read().split('\n')
  except:
    pass
  for line in lines:
    try:
      key, value = parse_key_value(line)
      if value != '':
        dot_emscripten[key] = value
#        print("Got '" + key + "' = '" + value + "'")
    except:
      pass


def generate_dot_emscripten(active_tools):
  global emscripten_config_directory
  if emscripten_config_directory == emsdk_path():
    temp_dir = sdk_path('tmp')
    mkdir_p(temp_dir)
    embedded = True
  else:
    temp_dir = tempfile.gettempdir().replace('\\', '/')
    embedded = False

  has_spidermonkey = False
  has_node = False

  cfg = 'import os\n'

  if embedded:
    cfg += "emsdk_path=os.path.dirname(os.environ.get('EM_CONFIG')).replace('\\\\', '/')\n"

  # Different tools may provide the same activated configs; the latest to be
  # activated is the relevant one.
  activated_keys_in_order = []
  activated_key_values = {}

  for tool in active_tools:
    tool_cfg = tool.activated_config()
    if tool_cfg:
      for specific_cfg in tool_cfg.split(';'):
        name, value = specific_cfg.split('=')
        if name not in activated_key_values:
          activated_keys_in_order.append(name)
        activated_key_values[name] = value

  for name in activated_keys_in_order:
    if name == 'SPIDERMONKEY_ENGINE':
      has_spidermonkey = True
    if name == 'NODE_JS':
      has_node = True
    cfg += name + ' = ' + activated_key_values[name] + '\n'

  # These two vars must always be defined, even though they might not exist.
  if not has_spidermonkey:
    cfg += "SPIDERMONKEY_ENGINE = ''\n"
  if not has_node:
    node_fallback = which('nodejs')
    if not node_fallback:
      node_fallback = 'node'
    cfg += "NODE_JS = '" + node_fallback + "'\n"

  cfg += '''V8_ENGINE = ''
TEMP_DIR = ''' + "'" + temp_dir + "'" + '''
COMPILER_ENGINE = NODE_JS
JS_ENGINES = [NODE_JS]
'''

  if embedded:
    cfg = cfg.replace(emscripten_config_directory, "' + emsdk_path + '")

  if os.path.exists(dot_emscripten_path()):
    backup_path = dot_emscripten_path() + ".old"
    print("Backing up old Emscripten configuration file in " + os.path.normpath(backup_path))
    move_with_overwrite(dot_emscripten_path(), backup_path)

  with open(dot_emscripten_path(), "w") as text_file:
    text_file.write(cfg)

  # Clear old cached emscripten content.
  try:
    remove_tree(os.path.join(emscripten_config_directory, ".emscripten_cache"))
    os.remove(os.path.join(emscripten_config_directory, ".emscripten_sanity"))
    os.remove(os.path.join(emscripten_config_directory, ".emscripten_cache__last_clear"))
  except:
    pass

  print("The Emscripten configuration file " + os.path.normpath(dot_emscripten_path()) + " has been rewritten with the following contents:")
  print('')
  print(cfg.strip())
  print('')

  path_add = get_required_path(active_tools)
  if not WINDOWS:
    emsdk_env = os.path.relpath(sdk_path('emsdk_env.sh'))
    if '/' not in emsdk_env:
      emsdk_env = './emsdk_env.sh'
    print("To conveniently access the selected set of tools from the command line, consider adding the following directories to PATH, or call 'source " + emsdk_env + "' to do this for you.")
    print('')
    print('   ' + ENVPATH_SEPARATOR.join(path_add))


def find_msbuild_dir():
  if 'ProgramFiles' in os.environ and os.environ['ProgramFiles']:
    program_files = os.environ['ProgramFiles']
  else:
    program_files = 'C:/Program Files'
  if 'ProgramFiles(x86)' in os.environ and os.environ['ProgramFiles(x86)']:
    program_files_x86 = os.environ['ProgramFiles(x86)']
  else:
    program_files_x86 = 'C:/Program Files (x86)'
  MSBUILDX86_DIR = os.path.join(program_files_x86, "MSBuild/Microsoft.Cpp/v4.0/Platforms")
  MSBUILD_DIR = os.path.join(program_files, "MSBuild/Microsoft.Cpp/v4.0/Platforms")
  if os.path.exists(MSBUILDX86_DIR):
    return MSBUILDX86_DIR
  elif os.path.exists(MSBUILD_DIR):
    return MSBUILD_DIR
  else:
    return '' # No MSbuild installed.


def get_installed_vstool_version(installed_path):
  try:
    return open(installed_path + "/version.txt", "r").read()
  except:
    return None


class Tool(object):
  def __init__(self, data):
    # Convert the dictionary representation of the tool in 'data' to members of this class for convenience.
    for key, value in data.items():
      # Python2 compat, convert unicode to str
      if sys.version_info < (3,) and isinstance(value, unicode): # noqa
        value = value.encode('Latin-1')
      setattr(self, key, value)

    # Cache the name ID of this Tool (these are read very often)
    self.name = self.id + '-' + self.version
    if hasattr(self, 'bitness'):
      self.name += '-' + str(self.bitness) + 'bit'

  def __str__(self):
    return self.name

  def __repr__(self):
    return self.name

  def expand_vars(self, str):
    if WINDOWS and '%MSBuildPlatformsDir%' in str:
      str = str.replace('%MSBuildPlatformsDir%', find_msbuild_dir())
    if '%cmake_build_type_on_win%' in str:
      str = str.replace('%cmake_build_type_on_win%', (decide_cmake_build_type(self) + '/') if WINDOWS else '')
    if '%installation_dir%' in str:
      str = str.replace('%installation_dir%', sdk_path(self.installation_dir()))
    if '%generator_prefix%' in str:
      str = str.replace('%generator_prefix%', cmake_generator_prefix())
    str = str.replace('%.exe%', '.exe' if WINDOWS else '')
    if '%fastcomp_build_dir%' in str:
      str = str.replace('%fastcomp_build_dir%', fastcomp_build_dir(self))
    if '%fastcomp_build_bin_dir%' in str:
      str = str.replace('%fastcomp_build_bin_dir%', fastcomp_build_bin_dir(self))
    return str

  # Return true if this tool requires building from source, and false if this is a precompiled tool.
  def needs_compilation(self):
    if hasattr(self, 'cmake_build_type'):
      return True

    if hasattr(self, 'uses'):
      for tool_name in self.uses:
        tool = find_tool(tool_name)
        if not tool:
          debug_print('Tool ' + str(self) + ' depends on ' + tool_name + ' which does not exist!')
          continue
        if tool.needs_compilation():
          return True

    return False

  # Specifies the target path where this tool will be installed to. This could either be a directory or a filename (e.g. in case of node.js)
  def installation_path(self):
    if WINDOWS and hasattr(self, 'windows_install_path'):
      pth = self.expand_vars(self.windows_install_path)
      return sdk_path(pth)
    if hasattr(self, 'install_path'):
      pth = self.expand_vars(self.install_path)
      return sdk_path(pth)
    p = self.version
    if hasattr(self, 'bitness') and (not hasattr(self, 'append_bitness') or self.append_bitness):
      p += '_' + str(self.bitness) + 'bit'
    return sdk_path(os.path.join(self.id, p))

  # Specifies the target directory this tool will be installed to.
  def installation_dir(self):
    dir = self.installation_path()
    if path_points_to_directory(dir):
      return dir
    else:
      return os.path.dirname(dir)

  # Returns the configuration item that needs to be added to .emscripten to make this Tool active for the current user.
  def activated_config(self):
    if hasattr(self, 'activated_cfg'):
      return to_unix_path(self.expand_vars(self.activated_cfg))
    else:
      return ''

  def activated_environment(self):
    if hasattr(self, 'activated_env'):
      return self.expand_vars(self.activated_env).split(';')
    else:
      return []

  def compatible_with_this_arch(self):
    if hasattr(self, 'arch'):
      if self.arch != ARCH:
        return False
    return True

  def compatible_with_this_os(self):
    if hasattr(self, 'os'):
      if self.os == 'all':
        return True
      if self.compatible_with_this_arch() and ((WINDOWS and 'win' in self.os) or (LINUX and ('linux' in self.os or 'unix' in self.os)) or (OSX and ('osx' in self.os or 'unix' in self.os))):
        return True
      else:
        return False
    else:
      if not hasattr(self, 'osx_url') and not hasattr(self, 'windows_url') and not hasattr(self, 'unix_url') and not hasattr(self, 'linux_url'):
        return True

    if OSX and hasattr(self, 'osx_url') and self.compatible_with_this_arch():
      return True

    if LINUX and hasattr(self, 'linux_url') and self.compatible_with_this_arch():
      return True

    if WINDOWS and (hasattr(self, 'windows_url') or hasattr(self, 'windows_install_path')) and self.compatible_with_this_arch():
      return True

    if UNIX and hasattr(self, 'unix_url'):
      return True

    return hasattr(self, 'url')

  def is_installed(self):
    # If this tool/sdk depends on other tools, require that all dependencies are installed for this tool to count as being installed.
    if hasattr(self, 'uses'):
      for tool_name in self.uses:
        tool = find_tool(tool_name)
        if tool is None:
          print("Manifest error: No tool by name '" + tool_name + "' found! This may indicate an internal SDK error!")
          return False
        if not tool.is_installed():
          return False

    if self.download_url() is not None:
      # For e.g. fastcomp clang from git repo, the activated PATH is the directory where the compiler is built to, and installation_path is
      # the directory where the source tree exists. To distinguish between multiple packages sharing the same source
      # (clang-master-32bit, clang-master-64bit, clang-incoming-32bit and clang-incoming-64bit each share the same git repo), require
      # that in addition to the installation directory, each item in the activated PATH must exist.
      activated_path = self.expand_vars(self.activated_path).split(';') if hasattr(self, 'activated_path') else [self.installation_path()]

      def each_path_exists(pathlist):
        for path in pathlist:
          if not os.path.exists(path):
            return False
        return True

      content_exists = os.path.exists(self.installation_path()) and each_path_exists(activated_path) and (os.path.isfile(self.installation_path()) or num_files_in_directory(self.installation_path()) > 0)

      if self.id == 'vs-tool': # vs-tool is a special tool since all versions must be installed to the same dir, so dir name will not differentiate the version.
        return content_exists and get_installed_vstool_version(self.installation_path()) == self.version
      elif hasattr(self, 'custom_is_installed_script'):
        if self.custom_is_installed_script == 'is_optimizer_installed':
          return is_optimizer_installed(self)
        elif self.custom_is_installed_script == 'is_binaryen_installed':
          return is_binaryen_installed(self)
        else:
          raise Exception('Unknown custom_is_installed_script directive "' + self.custom_is_installed_script + '"!')
      else:
        return content_exists
    else:
      return True # This tool does not contain downloadable elements, so it is installed by default.

  def is_active(self):
    if not self.is_installed():
      return False

    if self.id == 'vs-tool':
      return True # vs-tool is a special tool since all versions must be installed to the same dir, which means that if this tool is installed, it is also active.

    # All dependencies of this tool must be active as well.
    deps = self.dependencies()
    for tool in deps:
      if not tool.is_active():
        return False

    activated_cfg = self.activated_config()
    if activated_cfg == '':
      return len(deps) > 0

    activated_cfg = activated_cfg.split(';')
    for cfg in activated_cfg:
      cfg = cfg.strip()
      key, value = parse_key_value(cfg)
      if key not in dot_emscripten:
        debug_print(str(self) + ' is not active, because key="' + key + '" does not exist in .emscripten')
        return False

      # If running in embedded mode, all paths are stored dynamically relative to the emsdk root, so normalize those first.
      dot_emscripten_key = dot_emscripten[key].replace("' + emsdk_path + '", emsdk_path())
      if dot_emscripten_key != value:
        debug_print(str(self) + ' is not active, because key="' + key + '" has value "' + dot_emscripten_key + '" but should have value "' + value + '"')
        return False
    return True

  # Returns true if the system environment variables requires by this tool are currently active.
  def is_env_active(self):
    envs = self.activated_environment()
    for env in envs:
      key, value = parse_key_value(env)
      if key not in os.environ or to_unix_path(os.environ[key]) != to_unix_path(value):
        debug_print(str(self) + ' is not active, because environment variable key="' + key + '" has value "' + str(os.getenv(key)) + '" but should have value "' + value + '"')
        return False

    if hasattr(self, 'activated_path'):
      path = self.expand_vars(self.activated_path).replace('\\', '/')
      path = path.split(ENVPATH_SEPARATOR)
      for p in path:
        path_items = os.environ['PATH'].replace('\\', '/').split(ENVPATH_SEPARATOR)
        if not normalized_contains(path_items, p):
          debug_print(str(self) + ' is not active, because environment variable PATH item "' + p + '" is not present (PATH=' + os.environ['PATH'] + ')')
          return False
    return True

  def win_activate_env_vars(self, permanently_activate):
    if WINDOWS:
      envs = self.activated_environment()
      for env in envs:
        key, value = parse_key_value(env)

        if permanently_activate:
          win_delete_environment_variable(key, False) # If there is an env var for the LOCAL USER with same name, it will hide the system var, so must remove that first.

        win_set_environment_variable(key, value, permanently_activate)

  # If this tool can be installed on this system, this function returns True.
  # Otherwise, this function returns a string that describes the reason why this tool is not available.
  def can_be_installed(self):
    if hasattr(self, 'bitness'):
      if self.bitness == 64 and not is_os_64bit():
        return "this tool is only provided for 64-bit OSes"

    if self.id == 'vs-tool':
      msbuild_dir = find_msbuild_dir()
      if len(msbuild_dir) > 0:
        return True
      else:
        return "Visual Studio 2010 was not found"
    else:
      return True

  def download_url(self):
    if WINDOWS and hasattr(self, 'windows_url'):
      return self.windows_url
    elif OSX and hasattr(self, 'osx_url'):
      return self.osx_url
    elif LINUX and hasattr(self, 'linux_url'):
      return self.linux_url
    elif UNIX and hasattr(self, 'unix_url'):
      return self.unix_url
    elif hasattr(self, 'url'):
      return self.url
    else:
      return None

  def install(self):
    if self.can_be_installed() is not True:
      print("The tool '" + str(self) + "' is not available due to the reason: " + self.can_be_installed())
      return False

    if self.id == 'sdk':
      print("Installing SDK '" + str(self) + "'..")
      for tool_name in self.uses:
        tool = find_tool(tool_name)
        if tool is None:
          print("Manifest error: No tool by name '" + tool_name + "' found! This may indicate an internal SDK error!")
        success = tool.install()
        if not success:
          return False
      print("Done installing SDK '" + str(self) + "'.")
      return True
    else:
      print("Installing tool '" + str(self) + "'..")
      url = self.download_url()

      if hasattr(self, 'custom_install_script') and self.custom_install_script == 'build_fastcomp':
        success = build_llvm_tool(self)
      elif hasattr(self, 'git_branch'):
        success = git_clone_checkout_and_pull(url, self.installation_path(), self.git_branch)
      elif url.endswith(ARCHIVE_SUFFIXES):
        # TODO: explain the vs-tool special-casing
        download_even_if_exists = (self.id == 'vs-tool')
        # if we are downloading a zip, we will unpack and delete it after immediately anyhow,
        # so there is no need to look for an existing one (which may have been left behind
        # due to an error in the past)
        if url.endswith(ARCHIVE_SUFFIXES):
          download_even_if_exists = True
        filename_prefix = getattr(self, 'zipfile_prefix', '')
        success = download_and_unzip(url, self.installation_path(), download_even_if_exists=download_even_if_exists, filename_prefix=filename_prefix)
      else:
        dst_file = download_file(urljoin(emsdk_packages_url, self.download_url()), self.installation_path())
        if dst_file:
          success = True
        else:
          success = False

      if success:
        if hasattr(self, 'custom_install_script'):
          if self.custom_install_script == 'build_optimizer':
            success = build_optimizer_tool(self)
          elif self.custom_install_script == 'build_fastcomp':
            pass # 'build_fastcomp' is a special one that does the download on its own, others do the download manually.
          elif self.custom_install_script == 'build_binaryen':
            success = build_binaryen_tool(self)
          else:
            raise Exception('Unknown custom_install_script command "' + self.custom_install_script + '"!')

        # Install an emscripten-version.txt file if told to, and if there is one.
        # (If this is not an actual release, but some other build, then we do not
        # write anything.)
        if hasattr(self, 'emscripten_releases_hash'):
          emscripten_version_file_path = os.path.join(to_native_path(self.expand_vars(self.activated_path)), 'emscripten-version.txt')
          version = get_emscripten_release_version(self.emscripten_releases_hash)
          if version:
            open(emscripten_version_file_path, 'w').write('"%s"' % version)

      if not success:
        print("Installation failed!")
        return False
    print("Done installing tool '" + str(self) + "'.")

    # Sanity check that the installation succeeded, and if so, remove unneeded leftover installation files.
    if self.is_installed():
      self.cleanup_temp_install_files()
    else:
      print("Warning: The installation of '" + str(self) + "' seems to have failed, but no error was detected. Either something went wrong with the installation, or this may indicate an internal emsdk error.")
    return True

  def cleanup_temp_install_files(self):
    url = self.download_url()
    if url.endswith(ARCHIVE_SUFFIXES):
      download_target = get_download_target(url, zips_subdir, getattr(self, 'zipfile_prefix', ''))
      debug_print("Deleting temporary zip file " + download_target)
      rmfile(download_target)

  def uninstall(self):
    if not self.is_installed():
      print("Tool '" + str(self) + "' was not installed. No need to uninstall.")
      return
    print("Uninstalling tool '" + str(self) + "'..")
    if hasattr(self, 'custom_uninstall_script'):
      if self.custom_uninstall_script == 'uninstall_optimizer':
        uninstall_optimizer(self)
      elif self.custom_uninstall_script == 'uninstall_binaryen':
        uninstall_binaryen(self)
      else:
        raise Exception('Unknown custom_uninstall_script directive "' + self.custom_uninstall_script + '"!')
    try:
      print("Deleting path '" + self.installation_path() + "'")
      remove_tree(self.installation_path())
      os.remove(self.installation_path())
    except:
      pass
    print("Done uninstalling '" + str(self) + "'.")

  def dependencies(self):
    if not hasattr(self, 'uses'):
      return []
    deps = []

    for tool_name in self.uses:
      tool = find_tool(tool_name)
      if tool:
        deps += [tool]
    return deps

  def recursive_dependencies(self):
    if not hasattr(self, 'uses'):
      return []
    deps = []
    for tool_name in self.uses:
      tool = find_tool(tool_name)
      if tool:
        deps += [tool]
        deps += tool.recursive_dependencies()
    return deps


# A global registry of all known Emscripten SDK tools available in the SDK manifest.
tools = []
tools_map = {}


def add_tool(tool):
  tool.is_sdk = False
  tools.append(tool)
  if find_tool(str(tool)):
    raise Exception('Duplicate tool ' + str(tool) + '! Existing:\n{' + ', '.join("%s: %s" % item for item in vars(find_tool(str(tool))).items()) + '}, New:\n{' + ', '.join("%s: %s" % item for item in vars(tool).items()) + '}')
  tools_map[str(tool)] = tool


# A global registry of all known SDK toolsets.
sdks = []
sdks_map = {}


def add_sdk(sdk):
  sdk.is_sdk = True
  sdks.append(sdk)
  if find_sdk(str(sdk)):
    raise Exception('Duplicate sdk ' + str(sdk) + '! Existing:\n{' + ', '.join("%s: %s" % item for item in vars(find_sdk(str(sdk))).items()) + '}, New:\n{' + ', '.join("%s: %s" % item for item in vars(sdk).items()) + '}')
  sdks_map[str(sdk)] = sdk


# N.B. In both tools and sdks list above, we take the convention that the newest items are at the back of the list (ascending chronological order)

def find_tool(name):
  return tools_map.get(name)


def find_sdk(name):
  return sdks_map.get(name)


def is_os_64bit():
  # http://stackoverflow.com/questions/2208828/detect-64bit-os-windows-in-python
  return platform.machine().endswith('64')


def find_latest_releases_version():
  releases_info = load_releases_info()
  return releases_info['latest']


def find_latest_releases_hash():
  releases_info = load_releases_info()
  return releases_info['releases'][find_latest_releases_version()]


def find_latest_releases_sdk(which):
  return 'sdk-releases-%s-%s-64bit' % (which, find_latest_releases_hash())


def find_tot_sdk(which):
  if not os.path.exists(tot_path()):
    print('Tip-of-tree information was not found, run emsdk update-tags')
    sys.exit(1)
  tot = open(tot_path()).read()
  if not tot:
    print('Tip-of-tree build was not found, run emsdk update-tags (however, if there is no recent tip-of-tree build, you may need to wait)')
    sys.exit(1)
  return 'sdk-releases-%s-%s-64bit' % (which, tot)


# Given a git hash in emscripten-releases, find the emscripten
# version for it. There may not be one if this is not the hash of
# a release, in which case we return None.
def get_emscripten_release_version(emscripten_releases_hash):
  releases_info = load_releases_info()
  for key, value in dict(releases_info['releases']).items():
    if value == emscripten_releases_hash:
      return key
  return None


def tot_path():
  return sdk_path('emscripten-releases-tot.txt')


# Get the tip-of-tree build identifier.
def get_emscripten_releases_tot():
  git_clone_checkout_and_pull(emscripten_releases_repo, sdk_path('releases'), 'master')
  recent_releases = git_recent_commits(sdk_path('releases'))
  # The recent releases are the latest hashes in the git repo. There
  # may not be a build for the most recent ones yet; find the last
  # that does.
  for release in recent_releases:
    url = emscripten_releases_download_url_template % (
      os_name_for_emscripten_releases(),
      release,
      'tbz2' if not WINDOWS else 'zip'
    )
    try:
      urlopen(url)
    except:
      continue
    return release
  return ''


# Finds the best-matching python tool for use.
def find_used_python():
  for t in reversed(tools): # Find newest tool first - those are always at the end of the list.
    if t.id == 'python' and t.is_installed() and t.is_active() and t.is_env_active():
      return t
  for t in reversed(tools):
    if t.id == 'python' and t.is_installed() and t.is_active():
      return t
  for t in reversed(tools):
    if t.id == 'python' and t.is_installed():
      return t
  return None


def version_key(ver):
  return list(map(int, re.split('[._-]', ver)))


# A sort function that is compatible with both Python 2 and Python 3 using a custom comparison function.
def python_2_3_sorted(arr, cmp):
  if sys.version_info >= (3,):
    return sorted(arr, key=functools.cmp_to_key(cmp))
  else:
    return sorted(arr, cmp=cmp)


def fetch_emscripten_tags():
  git = GIT(must_succeed=False)

  if git:
    print('Fetching emscripten-releases repository...')
    emscripten_releases_tot = get_emscripten_releases_tot()
    if emscripten_releases_tot:
      open(tot_path(), 'w').write(emscripten_releases_tot)

#  Emscripten Nightlies support has been removed, clear the list of known Nightlies locally.
#  print('Fetching all precompiled Nightly versions..')
#  download_file('https://s3.amazonaws.com/mozilla-games/emscripten/packages/llvm/nightly/' + os_name() + '_32bit/index.txt', 'llvm-nightlies-32bit.txt', download_even_if_exists=True)
#  download_file('https://s3.amazonaws.com/mozilla-games/emscripten/packages/llvm/nightly/' + os_name() + '_64bit/index.txt', 'llvm-nightlies-64bit.txt', download_even_if_exists=True)
#  download_file('https://s3.amazonaws.com/mozilla-games/emscripten/packages/emscripten/nightly/' + os_name() + '/index.txt', 'emscripten-nightlies.txt', download_even_if_exists=True)
  for f in ['llvm-nightlies-32bit.txt', 'llvm-nightlies-64bit.txt', 'emscripten-nightlies.txt']:
    if os.path.isfile(f):
      os.remove(f)

  print('Fetching all precompiled tagged releases..')
  download_file('https://s3.amazonaws.com/mozilla-games/emscripten/packages/llvm/tag/' + os_name() + '_32bit/index.txt', 'llvm-tags-32bit.txt', download_even_if_exists=True)
  download_file('https://s3.amazonaws.com/mozilla-games/emscripten/packages/llvm/tag/' + os_name() + '_64bit/index.txt', 'llvm-tags-64bit.txt', download_even_if_exists=True)

  if not git:
    print('Update complete, however skipped fetching the Emscripten tags, since git was not found.')
    if WINDOWS:
      print("If you want to compile one of the tagged releases from source, please install git by typing 'emsdk install git-1.9.4', or alternatively by installing it manually from http://git-scm.com/downloads . If you install git manually, remember to add it to PATH.")
    elif OSX:
      print("If you want to compile one of the tagged releases from source, please install git from http://git-scm.com/ , or by installing XCode and then the XCode Command Line Tools (see http://stackoverflow.com/questions/9329243/xcode-4-4-command-line-tools ).")
    elif LINUX:
      print("If you want to compile one of the tagged releases from source, please install git using your package manager, see http://git-scm.com/book/en/Getting-Started-Installing-Git .")
    else:
      print("If you want to compile one of the tagged releases from source, please install git.")
    print("If you are not looking to build Emscripten from source, you can safely ignore this message.")
    return


def is_emsdk_sourced_from_github():
  return os.path.exists(os.path.join(emsdk_path(), '.git'))


def update_emsdk():
  if is_emsdk_sourced_from_github():
    print('You seem to have bootstrapped Emscripten SDK by cloning from GitHub. In this case, use "git pull" instead of "emsdk update" to update emsdk. (Not doing that automatically in case you have local changes)', file=sys.stderr)
    print('Alternatively, use "emsdk update-tags" to refresh the latest list of tags from the different Git repositories.', file=sys.stderr)
    sys.exit(1)
  if not download_and_unzip(emsdk_zip_download_url, emsdk_path(), download_even_if_exists=True):
    sys.exit(1)
  fetch_emscripten_tags()


# Lists all legacy (pre-emscripten-releases) tagged versions directly in the Git repositories. These we can pull and compile from source.
def load_legacy_emscripten_tags():
  try:
    return open(sdk_path('legacy-emscripten-tags.txt'), 'r').read().split('\n')
  except:
    return []


def load_legacy_binaryen_tags():
  try:
    return open(sdk_path('legacy-binaryen-tags.txt'), 'r').read().split('\n')
  except:
    return []


def remove_prefix(s, prefix):
  if s.startswith(prefix):
    return s[len(prefix):]
  else:
    return s


def remove_suffix(s, suffix):
  if s.endswith(suffix):
    return s[:len(s) - len(suffix)]
  else:
    return s


# filename should be one of: 'llvm-nightlies-32bit.txt', 'llvm-nightlies-64bit.txt', 'llvm-precompiled-tags-32bit.txt', 'llvm-precompiled-tags-64bit.txt', 'emscripten-nightlies.txt'
def load_file_index_list(filename):
  try:
    items = open(sdk_path(filename), 'r').read().split('\n')
    items = map(lambda x: remove_suffix(remove_suffix(remove_prefix(remove_prefix(x, 'emscripten-llvm-e'), 'emscripten-nightly-'), '.tar.gz'), '.zip').strip(), items)
    items = filter(lambda x: 'latest' not in x and len(x) > 0, items)

    # Sort versions from oldest to newest (the default sort would be lexicographic, i.e. '1.37.1 < 1.37.10 < 1.37.2')
    items = sorted(items, key=version_key)[::-1]

    return items
  except:
    return []


def load_llvm_32bit_nightlies():
  return load_file_index_list('llvm-nightlies-32bit.txt')


def load_llvm_64bit_nightlies():
  return load_file_index_list('llvm-nightlies-64bit.txt')


def load_emscripten_nightlies():
  return load_file_index_list('emscripten-nightlies.txt')


def load_llvm_precompiled_tags_32bit():
  return load_file_index_list('llvm-tags-32bit.txt')


def load_llvm_precompiled_tags_64bit():
  return load_file_index_list('llvm-tags-64bit.txt')


# Load the json info for emscripten-releases.
def load_releases_info():
  try:
    text = open(sdk_path('emscripten-releases-tags.txt'), 'r').read()
    return json.loads(text)
  except Exception as e:
    print('Error parsing emscripten-releases-tags.txt!')
    print(str(e))
    sys.exit(1)


# Get a list of tags for emscripten-releases.
def load_releases_tags():
  info = load_releases_info()
  tags = list(info['releases'].values())
  # Add the tip-of-tree, if it exists.
  if os.path.exists(tot_path()):
    tot = open(tot_path()).read()
    if tot:
      tags.append(tot)
  return tags


def load_releases_versions():
  info = load_releases_info()
  versions = list(info['releases'].keys())
  return versions


def is_string(s):
  if sys.version_info[0] >= 3:
    return isinstance(s, str)
  return isinstance(s, basestring)  # noqa


def load_sdk_manifest():
  global tools, sdks
  try:
    manifest = json.loads(open(sdk_path("emsdk_manifest.json"), "r").read())
  except Exception as e:
    print('Error parsing emsdk_manifest.json!')
    print(str(e))
    return

  emscripten_tags = load_legacy_emscripten_tags()
  llvm_precompiled_tags_32bit = list(reversed(load_llvm_precompiled_tags_32bit()))
  llvm_precompiled_tags_64bit = list(reversed(load_llvm_precompiled_tags_64bit()))
  llvm_precompiled_tags = llvm_precompiled_tags_32bit + llvm_precompiled_tags_64bit
  binaryen_tags = load_legacy_binaryen_tags()
  llvm_32bit_nightlies = list(reversed(load_llvm_32bit_nightlies()))
  llvm_64bit_nightlies = list(reversed(load_llvm_64bit_nightlies()))
  emscripten_nightlies = list(reversed(load_emscripten_nightlies()))
  releases_tags = load_releases_tags()

  def dependencies_exist(sdk):
    for tool_name in sdk.uses:
      tool = find_tool(tool_name)
      if not tool:
        return False
    return True

  def cmp_version(ver, cmp_operand, reference):
    if cmp_operand == '<=':
      return version_key(ver) <= version_key(reference)
    if cmp_operand == '<':
      return version_key(ver) < version_key(reference)
    if cmp_operand == '>=':
      return version_key(ver) >= version_key(reference)
    if cmp_operand == '>':
      return version_key(ver) > version_key(reference)
    if cmp_operand == '==':
      return version_key(ver) == version_key(reference)
    if cmp_operand == '!=':
      return version_key(ver) != version_key(reference)
    raise Exception('Invalid cmp_operand "' + cmp_operand + '"!')

  def passes_filters(param, ver, filters):
    for v in filters:
      if v[0] == param and not cmp_version(ver, v[1], v[2]):
        return False
    return True

  # A 'category parameter' is a %foo%-encoded identifier that specifies
  # a class of tools instead of just one tool, e.g. %tag% or %nightly..%
  def expand_category_param(param, category_list, t, is_sdk):
    for i, ver in enumerate(category_list):
      if not ver.strip():
        continue
      t2 = copy.copy(t)
      found_param = False
      for p, v in vars(t2).items():
        if is_string(v) and param in v:
          t2.__dict__[p] = v.replace(param, ver)
          found_param = True
      if not found_param:
        continue
      t2.is_old = i < len(category_list) - 2
      if hasattr(t2, 'uses'):
        t2.uses = [x.replace(param, ver) for x in t2.uses]

      # Filter out expanded tools by version requirements, such as ["tag", "<=", "1.37.22"]
      if hasattr(t2, 'version_filter'):
        passes = passes_filters(param, ver, t2.version_filter)
        if not passes:
          continue

      if is_sdk:
        if dependencies_exist(t2):
          if not find_sdk(t2.name):
            add_sdk(t2)
          else:
            debug_print('SDK ' + str(t2) + ' already existed in manifest, not adding twice')
      else:
        if not find_tool(t2.name):
          add_tool(t2)
        else:
          debug_print('Tool ' + str(t2) + ' already existed in manifest, not adding twice')

  for tool in manifest['tools']:
    t = Tool(tool)
    if t.compatible_with_this_os():
      if not hasattr(t, 'is_old'):
        t.is_old = False

      # Expand the metapackages that refer to tags or nightlies.
      if '%tag%' in t.version:
        expand_category_param('%tag%', emscripten_tags, t, is_sdk=False)
      elif '%precompiled_tag%' in t.version:
        expand_category_param('%precompiled_tag%', llvm_precompiled_tags, t, is_sdk=False)
      elif '%precompiled_tag32%' in t.version:
        expand_category_param('%precompiled_tag32%', llvm_precompiled_tags_32bit, t, is_sdk=False)
      elif '%precompiled_tag64%' in t.version:
        expand_category_param('%precompiled_tag64%', llvm_precompiled_tags_64bit, t, is_sdk=False)
      elif '%binaryen_tag%' in t.version:
        expand_category_param('%binaryen_tag%', binaryen_tags, t, is_sdk=False)
      elif '%nightly-llvm-64bit%' in t.version:
        expand_category_param('%nightly-llvm-64bit%', llvm_64bit_nightlies, t, is_sdk=False)
      elif '%nightly-llvm-32bit%' in t.version:
        expand_category_param('%nightly-llvm-32bit%', llvm_32bit_nightlies, t, is_sdk=False)
      elif '%nightly-emscripten%' in t.version:
        expand_category_param('%nightly-emscripten%', emscripten_nightlies, t, is_sdk=False)
      elif '%releases-tag%' in t.version:
        expand_category_param('%releases-tag%', releases_tags, t, is_sdk=False)
      else:
        add_tool(t)

  for sdk_str in manifest['sdks']:
    sdk_str['id'] = 'sdk'
    sdk = Tool(sdk_str)
    if sdk.compatible_with_this_os():
      if not hasattr(sdk, 'is_old'):
        sdk.is_old = False

      if '%tag%' in sdk.version:
        expand_category_param('%tag%', emscripten_tags, sdk, is_sdk=True)
      elif '%precompiled_tag%' in sdk.version:
        expand_category_param('%precompiled_tag%', llvm_precompiled_tags, sdk, is_sdk=True)
      elif '%precompiled_tag32%' in sdk.version:
        expand_category_param('%precompiled_tag32%', llvm_precompiled_tags_32bit, sdk, is_sdk=True)
      elif '%precompiled_tag64%' in sdk.version:
        expand_category_param('%precompiled_tag64%', llvm_precompiled_tags_64bit, sdk, is_sdk=True)
      elif '%nightly-llvm-64bit%' in sdk.version:
        expand_category_param('%nightly-llvm-64bit%', llvm_64bit_nightlies, sdk, is_sdk=True)
      elif '%nightly-llvm-32bit%' in sdk.version:
        expand_category_param('%nightly-llvm-32bit%', llvm_32bit_nightlies, sdk, is_sdk=True)
      elif '%nightly-emscripten%' in sdk.version:
        expand_category_param('%nightly-emscripten%', emscripten_nightlies, sdk, is_sdk=True)
      elif '%releases-tag%' in sdk.version:
        expand_category_param('%releases-tag%', releases_tags, sdk, is_sdk=True)
      else:
        add_sdk(sdk)


# Tests if the two given tools can be active at the same time.
# Currently only a simple check for name for same tool with different versions,
# possibly adds more logic in the future.
def can_simultaneously_activate(tool1, tool2):
  return tool1.id != tool2.id


def remove_nonexisting_tools(tool_list, log_errors=True):
  i = 0
  while i < len(tool_list):
    tool = tool_list[i]
    if not tool.is_installed():
      if log_errors:
        print("Warning: The SDK/tool '" + str(tool) + "' cannot be activated since it is not installed! Skipping this tool...")
      tool_list.pop(i)
      continue
    i += 1
  return tool_list


# Expands dependencies for each tool, and removes ones that don't exist.
def process_tool_list(tools_to_activate, log_errors=True):
  i = 0
  # Gather dependencies for each tool
  while i < len(tools_to_activate):
    tool = tools_to_activate[i]
    deps = tool.recursive_dependencies()
    tools_to_activate = tools_to_activate[:i] + deps + tools_to_activate[i:]
    i += len(deps) + 1

  tools_to_activate = remove_nonexisting_tools(tools_to_activate, log_errors=log_errors)

  # Remove conflicting tools
  i = 0
  while i < len(tools_to_activate):
    j = 0
    while j < i:
      secondary_tool = tools_to_activate[j]
      primary_tool = tools_to_activate[i]
      if not can_simultaneously_activate(primary_tool, secondary_tool):
        tools_to_activate.pop(j)
        j -= 1
        i -= 1
      j += 1
    i += 1
  return tools_to_activate


def run_emcc(tools_to_activate):
  for tool in tools_to_activate:
    activated_path = getattr(tool, 'activated_path', None)
    if activated_path and activated_path.endswith('/emscripten'):
      activated_path = to_native_path(tool.expand_vars(tool.activated_path))
      emcc_path = os.path.join(activated_path, 'emcc.py')
      if os.path.exists(emcc_path):
        debug_print('Calling emcc to initialize it')
        subprocess.call([sys.executable, emcc_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return


def emscripten_cache_directory():
  return os.path.join(emscripten_config_directory, ".emscripten_cache")


# Copy over any emscripten cache contents that were pregenerated. This avoids the user
# needing to immediately build libc etc. on first run.
def copy_pregenerated_cache(tools_to_activate):
  for tool in tools_to_activate:
    pregenerated_cache = getattr(tool, 'pregenerated_cache', None)
    if pregenerated_cache:
      # Finish the install of an emscripten-releases build.
      install_path = to_native_path(sdk_path(tool.expand_vars(tool.install_path)))
      in_cache = os.path.join(install_path, 'lib', pregenerated_cache)
      if os.path.exists(in_cache):
        out_cache = os.path.join(emscripten_cache_directory(), pregenerated_cache)
        os.makedirs(out_cache)
        for filename in os.listdir(in_cache):
          debug_print('Copying ' + filename + ' to cache dir')
          shutil.copy2(os.path.join(in_cache, filename),
                       os.path.join(out_cache, filename))


# Reconfigure .emscripten to choose the currently activated toolset, set PATH and other environment variables.
# Returns the full list of deduced tools that are now active.
def set_active_tools(tools_to_activate, permanently_activate):
  tools_to_activate = process_tool_list(tools_to_activate, log_errors=True)

  generate_dot_emscripten(tools_to_activate)

  # Generating .emscripten will cause emcc to clear the cache on first run (emcc sees that the file has
  # changed, since we write it here in the emsdk, and it never saw it before; so it clears the cache
  # as it assumes a new config file means system libraries may need rebuilding). To avoid emcc's clearing
  # wiping out the pregenerated cache contents we want to copy in, run emcc here, then copy the cache
  # contents.
  run_emcc(tools_to_activate)

  copy_pregenerated_cache(tools_to_activate)

  # Construct a .bat script that will be invoked to set env. vars and PATH
  if WINDOWS:
    env_string = construct_env(tools_to_activate, False)
    open(EMSDK_SET_ENV, 'w').write(env_string)

  # Apply environment variables to global all users section.
  if WINDOWS and permanently_activate:
    # Individual env. vars
    for tool in tools_to_activate:
      tool.win_activate_env_vars(permanently_activate=True)

    # PATH variable
    newpath, added_items = adjusted_path(tools_to_activate, system_path_only=True)
    if newpath != os.environ['PATH']: # Are there any actual changes?
      win_set_environment_variable('PATH', newpath, system=True)

  if len(tools_to_activate) > 0:
    tools = [x for x in tools_to_activate if not x.is_sdk]
    print('\nSet the following tools as active:\n   ' + '\n   '.join(map(lambda x: str(x), tools)))
    print('')
  return tools_to_activate


def currently_active_sdk():
  for sdk in reversed(sdks):
    if sdk.is_active():
      return sdk
  return None


def currently_active_tools():
  active_tools = []
  for tool in tools:
    if tool.is_active():
      active_tools += [tool]
  return active_tools


# http://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-in-python-whilst-preserving-order
def unique_items(seq):
  seen = set()
  seen_add = seen.add
  return [x for x in seq if x not in seen and not seen_add(x)]


# Tests if a path is contained in the given list, but with separators normalized.
def normalized_contains(lst, elem):
  elem = to_unix_path(elem)
  for e in lst:
    if elem == to_unix_path(e):
      return True
  return False


def to_msys_path(p):
  p = to_unix_path(p)
  new_path = re.sub(r'([a-zA-Z]):/(.*)', r'/\1/\2', p)
  if len(new_path) > 3 and new_path[0] == '/' and new_path[2] == '/':
    new_path = new_path[0] + new_path[1].lower() + new_path[2:]
  return new_path


# Looks at the current PATH and adds and removes entries so that the PATH reflects
# the set of given active tools.
def adjusted_path(tools_to_activate, log_additions=False, system_path_only=False):
  # These directories should be added to PATH
  path_add = get_required_path(tools_to_activate)
  # These already exist.
  if WINDOWS and not MSYS:
    existing_path = win_get_environment_variable('PATH', system=True)
    if not system_path_only:
      current_user_path = win_get_environment_variable('PATH', system=False)
      if current_user_path:
        existing_path += ENVPATH_SEPARATOR + current_user_path
    existing_path = existing_path.split(ENVPATH_SEPARATOR)

    # Fix up after potential changes made by bug https://github.com/kripken/emscripten/issues/4121
    system_root = os.environ['SystemRoot'].lower()
    for i in range(len(existing_path)):
      p = existing_path[i]
      if p.lower() == system_root:
        p = '%SystemRoot%'
      elif (system_root + '\\system32') in p.lower():
        p = '%SystemRoot%\\system32'
      elif (system_root + '\\system32\\wbem') in p.lower():
        p = '%SystemRoot%\\System32\\Wbem'
      elif (system_root + '\\system32\\windowspowershell\v1.0') in p.lower():
        p = '%SystemRoot%\\System32\\WindowsPowerShell\v1.0\\'
      existing_path[i] = p
  else:
    existing_path = os.environ['PATH'].split(ENVPATH_SEPARATOR)
  emsdk_root_path = to_unix_path(emsdk_path())

  existing_emsdk_tools = [item for item in existing_path if to_unix_path(item).startswith(emsdk_root_path)]
  new_emsdk_tools = [item for item in path_add if not normalized_contains(existing_emsdk_tools, item)]

  # Existing non-emsdk tools
  existing_path = [item for item in existing_path if not to_unix_path(item).startswith(emsdk_root_path)]
  new_path = [item for item in path_add if not normalized_contains(existing_path, item)]
  whole_path = unique_items(new_path + existing_path)
  if MSYS:
    # XXX Hack: If running native Windows Python in MSYS prompt where PATH entries look like "/c/Windows/System32", os.environ['PATH']
    # in Python will transform to show them as "C:\\Windows\\System32", so need to reconvert path delimiter back to forward slashes.
    whole_path = list(map(to_msys_path, whole_path))
    new_emsdk_tools = list(map(to_msys_path, new_emsdk_tools))

  return ((':' if MSYS else ENVPATH_SEPARATOR).join(whole_path), new_emsdk_tools)


def construct_env(tools_to_activate, permanent):
  global emscripten_config_directory
  env_string = ''
  newpath, added_path = adjusted_path(tools_to_activate)

# Dont permanently add to PATH, since this will break the whole system if there are more than 1024 chars in PATH.
# (SETX truncates to set only 1024 chars)
#  if permanent:
#    print('SETX PATH "' + newpath + '"')
#  else:

  if os.environ['PATH'] != newpath: # Don't bother setting the path if there are no changes.
    if POWERSHELL:
      env_string += '$env:PATH="' + newpath + '"\n'
    elif WINDOWS and not MSYS:
      env_string += 'SET PATH=' + newpath + '\n'
    else:
      env_string += 'export PATH="' + newpath + '"\n'
    if len(added_path) > 0:
      print('Adding directories to PATH:')
      for item in added_path:
        print('PATH += ' + item)
      print('')

  env_vars_to_add = []

  # A core variable EMSDK points to the root of Emscripten SDK directory.
  env_vars_to_add += [('EMSDK', to_unix_path(emsdk_path()))]

  em_config_path = os.path.normpath(dot_emscripten_path())
  if 'EM_CONFIG' not in os.environ or to_unix_path(os.environ['EM_CONFIG']) != to_unix_path(em_config_path):
    env_vars_to_add += [('EM_CONFIG', em_config_path)]
  if emscripten_config_directory == emsdk_path():
    em_cache_dir = sdk_path('.emscripten_cache')
    if 'EM_CACHE' not in os.environ or to_unix_path(os.environ['EM_CACHE']) != to_unix_path(em_cache_dir):
      env_vars_to_add += [('EM_CACHE', em_cache_dir)]
    mkdir_p(em_cache_dir)

  for tool in tools_to_activate:
    envs = tool.activated_environment()
    for env in envs:
      key, value = parse_key_value(env)
      value = to_native_path(tool.expand_vars(value))
      if key not in os.environ or to_unix_path(os.environ[key]) != to_unix_path(value): # Don't set env. vars which are already set to the correct value.
        env_vars_to_add += [(key, value)]

  if len(env_vars_to_add) > 0:
    print('Setting environment variables:')
    for key, value in env_vars_to_add:
      if POWERSHELL:
        env_string += '$env:' + key + '="' + value + '"\n'
      elif WINDOWS and not MSYS:
        if permanent:
          env_string += 'SETX ' + key + ' "' + value + '"\n'
        else:
          env_string += 'SET ' + key + '=' + value + '\n'
      else:
        env_string += 'export ' + key + '="' + value + '"\n'
      print(key + ' = ' + value)
    print('')
  return env_string


def silentremove(filename):
  try:
    os.remove(filename)
  except OSError as e:
    if e.errno != errno.ENOENT:
      raise


def main():
  global emscripten_config_directory, BUILD_FOR_TESTING, ENABLE_LLVM_ASSERTIONS, TTY_OUTPUT

  if len(sys.argv) <= 1 or sys.argv[1] == 'help' or sys.argv[1] == '--help':
    if len(sys.argv) <= 1:
      print(' emsdk: No command given. Please call one of the following:')
    else:
      print(' emsdk: Available commands:')

    print('''
   emsdk list [--old] [--uses]  - Lists all available SDKs and tools and their
                                  current installation status. With the --old
                                  parameter, also historical versions are
                                  shown. If --uses is passed, displays the
                                  composition of different SDK packages and
                                  dependencies.

   emsdk update                 - Updates emsdk to the newest version, and also
                                  runs 'update-tags' (below). If you have
                                  bootstrapped emsdk via cloning directly from
                                  GitHub, call "git pull" instead to update emsdk.

   emsdk update-tags            - Fetches the most up to date list of available
                                  Emscripten tagged and other releases from the
                                  servers.

   emsdk install [options] <tool 1> <tool 2> <tool 3> ...
                                - Downloads and installs given tools or SDKs.
                                  Options can contain:

                         -j<num>: Specifies the number of cores to use when
                                  building the tool. Default: use one less
                                  than the # of detected cores.

                  --build=<type>: Controls what kind of build of LLVM to
                                  perform. Pass either 'Debug', 'Release',
                                  'MinSizeRel' or 'RelWithDebInfo'. Default:
                                  'Release' for LLVM master branch, and
                                  'RelWithDebInfo' for LLVM incoming branch.

              --generator=<type>: Specifies the CMake Generator to be used
                                  during the build. Possible values are the
                                  same as what your CMake supports and whether
                                  the generator is valid depends on the tools
                                  you have installed. Defaults to 'Unix Makefiles'
                                  on *nix systems. If generator name is multiple
                                  words, enclose with single or double quotes.

                       --shallow: When installing tools from one of the git
                                  development branches 'master' or 'incoming',
                                  this parameter can be passed to perform a
                                  shallow git clone instead of a full one.
                                  This reduces the amount of network transfer
                                  that is needed. This option should only be
                                  used when you are interested in downloading
                                  one of the development branches, but are not
                                  looking to develop Emscripten yourself.
                                  Default: disabled, i.e. do a full clone.

                   --build-tests: If enabled, LLVM is built with internal tests
                                  included. Pass this to enable running test
                                  other.test_llvm_lit in the Emscripten test
                                  suite. Default: disabled.
             --enable-assertions: If specified, LLVM is built with assert()
                                  checks enabled. Useful for development
                                  purposes. Default: Enabled for 'incoming'
                                  branch, disabled for 'master' branch.
            --disable-assertions: Forces assertions off during the build.

      --vs2013/--vs2015/--vs2017: If building from source, overrides to build
                                  using the specified compiler. When installing
                                  precompiled packages, this has no effect.
                                  Note: The same compiler specifier must be
                                  passed to the emsdk activate command to
                                  activate the desired version.

                                  Notes on building from source:

                                  To pass custom CMake directives when configuring
                                  LLVM build, specify the environment variable
                                  LLVM_CMAKE_ARGS="param1=value1,param2=value2"
                                  in the environment where the build is invoked.
                                  See README.md for details.

   emsdk uninstall <tool/sdk>   - Removes the given tool or SDK from disk.''')

    if WINDOWS:
      print('''
   emsdk activate [--global] [--embedded] [--build=type] [--vs2013/--vs2015/--vs2017] <tool/sdk>

                                - Activates the given tool or SDK in the
                                  environment of the current shell. If the
                                  --global option is passed, the registration
                                  is done globally to all users in the system
                                  environment. If the --embedded option is
                                  passed, all Emcripten configuration files as
                                  well as the temp, cache and ports directories
                                  are located inside the Emscripten SDK
                                  directory rather than the user home
                                  directory. If a custom compiler version was
                                  used to override the compiler to use, pass
                                  the same --vs2013/--vs2015/--vs2017 parameter
                                  here to choose which version to activate.

   emcmdprompt.bat              - Spawns a new command prompt window with the
                                  Emscripten environment active.''')
    else:
      print('''   emsdk activate [--embedded] [--build=type] <tool/sdk>

                                - Activates the given tool or SDK in the
                                  environment of the current shell. If the
                                  --embedded option is passed, all Emcripten
                                  configuration files as well as the temp, cache
                                  and ports directories are located inside the
                                  Emscripten SDK directory rather than the user
                                  home directory.''')

    print('''
       Both commands 'install' and 'activate' accept an optional parameter
       '--build=type', which can be used to override what kind of installation
       or activation to perform. Possible values for type are Debug, Release,
       MinSizeRel or RelWithDebInfo. Note: When overriding a custom build type,
       be sure to match the same --build= option to both 'install' and
       'activate' commands and the invocation of 'emsdk_env', or otherwise
       these commands will default to operating on the default build types,
       which are Release for the 'master' SDK, and RelWithDebInfo for the
       'incoming' SDK.''')
    return 1

  # Extracts a boolean command line argument from sys.argv and returns True if it was present
  def extract_bool_arg(name):
    old_argv = sys.argv
    sys.argv = list(filter(lambda a: a != name, sys.argv))
    return len(sys.argv) != len(old_argv)

  arg_old = extract_bool_arg('--old')
  arg_uses = extract_bool_arg('--uses')
  arg_global = extract_bool_arg('--global')
  arg_embedded = extract_bool_arg('--embedded')
  arg_notty = extract_bool_arg('--notty')
  if arg_notty:
    TTY_OUTPUT = False

  cmd = sys.argv[1]

  # On first run when tag list is not present, populate it to bootstrap.
  if (cmd == 'install' or cmd == 'list') and not os.path.isfile(sdk_path('llvm-tags-64bit.txt')):
    fetch_emscripten_tags()

  load_dot_emscripten()
  load_sdk_manifest()

  # Process global args
  for i in range(2, len(sys.argv)):
    if sys.argv[i].startswith('--generator='):
      build_generator = re.match(r'''^--generator=['"]?([^'"]+)['"]?$''', sys.argv[i])
      if build_generator:
        global CMAKE_GENERATOR
        CMAKE_GENERATOR = build_generator.group(1)
        sys.argv[i] = ''
      else:
        print("Cannot parse CMake generator string: " + sys.argv[i] + ". Try wrapping generator string with quotes", file=sys.stderr)
        return 1
    elif sys.argv[i].startswith('--build='):
      build_type = re.match(r'^--build=(.+)$', sys.argv[i])
      if build_type:
        global CMAKE_BUILD_TYPE_OVERRIDE
        build_type = build_type.group(1)
        build_types = ['Debug', 'MinSizeRel', 'RelWithDebInfo', 'Release']
        try:
          build_type_index = [x.lower() for x in build_types].index(build_type.lower())
          CMAKE_BUILD_TYPE_OVERRIDE = build_types[build_type_index]
          sys.argv[i] = ''
        except:
          print('Unknown CMake build type "' + build_type + '" specified! Please specify one of ' + str(build_types), file=sys.stderr)
          return 1
      else:
        print("Invalid command line parameter " + sys.argv[i] + ' specified!', file=sys.stderr)
        return 1
  sys.argv = [x for x in sys.argv if not len(x) == 0]

  releases_info = load_releases_info()['releases']

  # Replace meta-packages with the real package names.
  if cmd in ('update', 'install', 'activate'):
    for i in range(2, len(sys.argv)):
      arg = sys.argv[i]
      if arg in ('latest', 'sdk-latest', 'latest-64bit', 'sdk-latest-64bit', 'latest-fastcomp', 'latest-releases-fastcomp'):
        sys.argv[i] = str(find_latest_releases_sdk('fastcomp'))
      elif arg in ('latest-upstream', 'latest-clang-upstream', 'latest-releases-upstream'):
        sys.argv[i] = str(find_latest_releases_sdk('upstream'))
      elif arg == 'tot-upstream':
        sys.argv[i] = str(find_tot_sdk('upstream'))
      elif arg in ('tot-fastcomp', 'sdk-nightly-latest'):
        sys.argv[i] = str(find_tot_sdk('fastcomp'))
      else:
        # check if it's a release handled by an emscripten-releases version,
        # and if so use that by using the right hash. we support a few notations,
        #   x.y.z[-(upstream|fastcomp_])
        #   sdk-x.y.z[-(upstream|fastcomp_])-64bit
        # TODO: support short notation for old builds too?
        upstream = False
        if '-upstream' in arg:
          arg = arg.replace('-upstream', '')
          upstream = True
        elif '-fastcomp' in arg:
          arg = arg.replace('-fastcomp', '')
          upstream = False
        arg = arg.replace('sdk-', '').replace('-64bit', '').replace('tag-', '')
        release_hash = releases_info.get(arg, None) or releases_info.get('sdk-' + arg + '-64bit')
        if release_hash:
          sys.argv[i] = 'sdk-releases-%s-%s-64bit' % ('upstream' if upstream else 'fastcomp', release_hash)

  if cmd == 'list':
    print('')

    if (LINUX or OSX or WINDOWS) and (ARCH == 'x86' or ARCH == 'x86_64'):
      print('The *recommended* precompiled SDK download is %s (%s).' % (find_latest_releases_version(), find_latest_releases_hash()))
      print()
      print('To install/activate it, use one of:')
      print('         latest                  [default (fastcomp) backend]')
      print('         latest-upstream         [upstream LLVM wasm backend]')
      print('')
      print('Those are equivalent to installing/activating the following:')
      print('         %s' % find_latest_releases_version())
      print('         %s-upstream' % find_latest_releases_version())
      print('')
    else:
      print('Warning: your platform does not have precompiled SDKs available.')
      print('You may install components from source.')
      print('')

    print('All recent (non-legacy) installable versions are:')
    releases_versions = sorted(load_releases_versions())
    releases_versions.reverse()
    for ver in releases_versions:
      print('         %s' % ver)
      print('         %s-upstream' % ver)
    print()

    has_partially_active_tools = [False] # Use array to work around the lack of being able to mutate from enclosing function.

    if len(sdks) > 0:
      def find_sdks(needs_compilation):
        s = []
        for sdk in sdks:
          if sdk.is_old and not arg_old:
            continue
          if sdk.needs_compilation() == needs_compilation:
            s += [sdk]
        return s

      def print_sdks(s):
        for sdk in s:
          installed = '\tINSTALLED' if sdk.is_installed() else ''
          active = '*' if sdk.is_active() else ' '
          print('    ' + active + '    {0: <25}'.format(str(sdk)) + installed)
          if arg_uses:
            for dep in sdk.uses:
              print('          - {0: <25}'.format(dep))
        print('')
      print('The additional following precompiled SDKs are also available for download:')
      print_sdks(find_sdks(False))

      print('The following SDKs can be compiled from source:')
      print_sdks(find_sdks(True))

    if len(tools) > 0:
      def find_tools(needs_compilation):
        t = []
        for tool in tools:
          if tool.is_old and not arg_old:
            continue
          if tool.needs_compilation() != needs_compilation:
            continue
          t += [tool]
        return t

      def print_tools(t):
        for tool in t:
          if tool.is_old and not arg_old:
            continue
          if tool.can_be_installed() is True:
            installed = '\tINSTALLED' if tool.is_installed() else ''
          else:
            installed = '\tNot available: ' + tool.can_be_installed()
          tool_is_active = tool.is_active()
          tool_is_env_active = tool_is_active and tool.is_env_active()
          if tool_is_env_active:
            active = ' * '
          elif tool_is_active:
            active = '(*)'
            has_partially_active_tools[0] = has_partially_active_tools[0] or True
          else:
            active = '   '
          print('    ' + active + '    {0: <25}'.format(str(tool)) + installed)
        print('')

      print('The following precompiled tool packages are available for download:')
      print_tools(find_tools(needs_compilation=False))
      print('The following tools can be compiled from source:')
      print_tools(find_tools(needs_compilation=True))
    else:
      if is_emsdk_sourced_from_github():
        print("There are no tools available. Run 'git pull' followed by 'emsdk update-tags' to fetch the latest set of tools.")
      else:
        print("There are no tools available. Run 'emsdk update' to fetch the latest set of tools.")
      print('')

    print('Items marked with * are activated for the current user.')
    if has_partially_active_tools[0]:
      env_cmd = 'emsdk_env.bat' if WINDOWS else 'source ./emsdk_env.sh'
      print('Items marked with (*) are selected for use, but your current shell environment is not configured to use them. Type "' + env_cmd + '" to set up your current shell to use them' + (', or call "emsdk activate --global <name_of_sdk>" to permanently activate them.' if WINDOWS else '.'))
    if not arg_old:
      print('')
      print("To access the historical archived versions, type 'emsdk list --old'")

    print('')
    if is_emsdk_sourced_from_github():
      print('Run "git pull" followed by "./emsdk update-tags" to pull in the latest list.')
    else:
      print('Run "./emsdk update" to pull in the latest list.')

    return 0
  elif cmd == 'construct_env':
    if len(sys.argv) == 2:
      outfile = EMSDK_SET_ENV
      silentremove(EMSDK_SET_ENV) # Clean up old temp file up front, in case of failure later before we get to write out the new one.
    else:
      outfile = sys.argv[2]
    tools_to_activate = currently_active_tools()
    tools_to_activate = process_tool_list(tools_to_activate, log_errors=True)
    env_string = construct_env(tools_to_activate, len(sys.argv) >= 3 and 'perm' in sys.argv[2])
    open(outfile, 'w').write(env_string)
    if UNIX:
      os.chmod(outfile, 0o755)
    return 0
  elif cmd == 'update':
    update_emsdk()
    silentremove(sdk_path(EMSDK_SET_ENV)) # Clean up litter after old emsdk update which may have left this temp file around.
    return 0
  elif cmd == 'update-tags':
    fetch_emscripten_tags()
    return 0
  elif cmd == 'activate':
    if arg_global:
      print('Registering active Emscripten environment globally for all users.')
      print('')
    if arg_embedded:
      # Activating the emsdk tools locally relative to Emscripten SDK directory.
      emscripten_config_directory = emsdk_path()
      print('Writing .emscripten configuration file to Emscripten SDK directory ' + emscripten_config_directory)
    else:
      print('Writing .emscripten configuration file to user home directory ' + emscripten_config_directory)
      # Remove .emscripten from emsdk dir, since its presence is used to detect whether emsdk is activate in embedded mode or not.
      try:
        os.remove(os.path.join(emsdk_path(), ".emscripten"))
      except:
        pass

    sys.argv = [x for x in sys.argv if not x.startswith('--')]

    tools_to_activate = currently_active_tools()
    for i in range(2, len(sys.argv)):
      tool = find_tool(sys.argv[i])
      if tool is None:
        tool = find_sdk(sys.argv[i])
      if tool is None:
        print("Error: No tool or SDK found by name '" + sys.argv[i] + "'.")
        return 1
      tools_to_activate += [tool]
    if len(tools_to_activate) == 0:
      print('No tools/SDKs specified to activate! Usage:\n   emsdk activate tool/sdk1 [tool/sdk2] [...]')
      return 1
    tools_to_activate = set_active_tools(tools_to_activate, permanently_activate=arg_global)
    if len(tools_to_activate) == 0:
      print('No tools/SDKs found to activate! Usage:\n   emsdk activate tool/sdk1 [tool/sdk2] [...]')
      return 1
    if WINDOWS and not arg_global:
      print('The changes made to environment variables only apply to the currently running shell instance. Use the \'emsdk_env.bat\' to re-enter this environment later, or if you\'d like to permanently register this environment globally to all users in Windows Registry, rerun this command with the option --global.')
    return 0
  elif cmd == 'install':
    # Process args
    for i in range(2, len(sys.argv)):
      if sys.argv[i].startswith('-j'):
        multicore = re.match(r'^-j(\d+)$', sys.argv[i])
        if multicore:
          global CPU_CORES
          CPU_CORES = int(multicore.group(1))
          sys.argv[i] = ''
        else:
          print("Invalid command line parameter " + sys.argv[i] + ' specified!', file=sys.stderr)
          return 1
      elif sys.argv[i] == '--shallow':
        global GIT_CLONE_SHALLOW
        GIT_CLONE_SHALLOW = True
        sys.argv[i] = ''
      elif sys.argv[i] == '--build-tests':
        BUILD_FOR_TESTING = True
        sys.argv[i] = ''
      elif sys.argv[i] == '--enable-assertions':
        ENABLE_LLVM_ASSERTIONS = 'ON'
        sys.argv[i] = ''
      elif sys.argv[i] == '--disable-assertions':
        ENABLE_LLVM_ASSERTIONS = 'OFF'
        sys.argv[i] = ''
    sys.argv = [x for x in sys.argv if not len(x) == 0]
    if len(sys.argv) <= 2:
      print("Missing parameter. Type 'emsdk install <tool name>' to install a tool or an SDK. Type 'emsdk list' to obtain a list of available tools. Type 'emsdk install latest' to automatically install the newest version of the SDK.")
      return 1
    for t in sys.argv[2:]:
      tool = find_tool(t)
      if tool is None:
        tool = find_sdk(t)
      if tool is None:
        print("Error: No tool or SDK found by name '" + t + "'.")
        return 1
      success = tool.install()
      if not success:
        return 1
    return 0
  elif cmd == 'uninstall':
    if len(sys.argv) <= 2:
      print("Syntax error. Call 'emsdk uninstall <tool name>'. Call 'emsdk list' to obtain a list of available tools.")
      return 1
    tool = find_tool(sys.argv[2])
    if tool is None:
      print("Error: Tool by name '" + sys.argv[2] + "' was not found.")
      return 1
    tool.uninstall()
    return 0

  print("Unknown command '" + cmd + "' given! Type 'emsdk help' to get a list of commands.")
  return 1


if __name__ == '__main__':
  sys.exit(main())
