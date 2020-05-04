#!/usr/bin/env python3
# Copyright 2020 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

"""Updates the python binaries that we cache store at
http://storage.google.com/webassembly.

Currently this is windows only and we rely on the system python on other
platforms.

We currently bundle a version of python for windows use the following
recipe:
  1. Download the "embeddable zip file" version of python from python.org
  2. Remove .pth file to work around https://bugs.python.org/issue34841
  3. Download and install pywin32 in the `site-packages` directory
  4. Re-zip and upload to storage.google.com
"""

import urllib.request
import subprocess
import os
import shutil
import sys

version = '3.7.4'
base = 'https://www.python.org/ftp/python/%s/' % version

pywin32_version = '227'
pywin32_base = 'https://github.com/mhammond/pywin32/releases/download/b%s/' % pywin32_version

upload_base = 'gs://webassembly/emscripten-releases-builds/deps/'


def make_python_patch(arch):
    if arch == 'amd64':
      pywin32_filename = 'pywin32-%s.win-%s-py3.7.exe' % (pywin32_version, arch)
    else:
      pywin32_filename = 'pywin32-%s.%s-py3.7.exe' % (pywin32_version, arch)
    filename = 'python-%s-embed-%s.zip' % (version, arch)
    out_filename = 'python-%s-embed-%s+pywin32.zip' % (version, arch)
    if not os.path.exists(pywin32_filename):
        download_url = pywin32_base + pywin32_filename
        print('Downloading pywin32: ' + download_url)
        urllib.request.urlretrieve(download_url, pywin32_filename)

    if not os.path.exists(filename):
        download_url = base + filename
        print('Downloading python: ' + download_url)
        urllib.request.urlretrieve(download_url, filename)

    os.mkdir('python-embed')
    subprocess.check_call(['unzip', '-q', os.path.abspath(filename)], cwd='python-embed')
    os.remove(os.path.join('python-embed', 'python37._pth'))

    os.mkdir('pywin32')
    rtn = subprocess.call(['unzip', '-q', os.path.abspath(pywin32_filename)], cwd='pywin32')
    assert rtn in [0, 1]

    os.mkdir(os.path.join('python-embed', 'lib'))
    shutil.move(os.path.join('pywin32', 'PLATLIB'), os.path.join('python-embed', 'lib', 'site-packages'))

    subprocess.check_call(['zip', '-rq', os.path.join('..', out_filename), '.'], cwd='python-embed')

    upload_url = upload_base + out_filename
    print('Uploading: ' + upload_url)
    cmd = ['gsutil', 'cp', '-n', out_filename, upload_url]
    print(' '.join(cmd))
    subprocess.check_call(cmd)

    # cleanup if everything went fine
    shutil.rmtree('python-embed')
    shutil.rmtree('pywin32')


def main():
    for arch in ('amd64', 'win32'):
        make_python_patch(arch)

    return 0


if __name__ == '__main__':
  sys.exit(main())
