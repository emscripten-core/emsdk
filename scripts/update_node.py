#!/usr/bin/env python3
# Copyright 2020 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

"""Updates the node binaries that we cache store at
http://storage.google.com/webassembly.
"""

import argparse
import os
import subprocess
import urllib.request

# When adjusting this version, visit
# https://github.com/nodejs/node/blob/v24.x/BUILDING.md#platform-list
# to verify minimum supported OS versions. Replace "v24.x" in the URL
# with the version field.
version = '24.19.0'
base = f'https://nodejs.org/dist/v{version}/'
upload_base = 'gs://webassembly/emscripten-releases-builds/deps/'

suffixes = [
    '-win-x64.zip',
    '-win-arm64.zip',
    '-darwin-x64.tar.gz',
    '-darwin-arm64.tar.gz',
    '-linux-x64.tar.xz',
    '-linux-arm64.tar.xz',
    '-linux-s390x.tar.gz',
]


def main():
  parser = argparse.ArgumentParser(description=__doc__)
  parser.add_argument('--upload', action='store_true', help='Upload binaries to Google Cloud Storage')
  args = parser.parse_args()

  for suffix in suffixes:
    filename = 'node-v%s%s' % (version, suffix)
    download_url = base + filename
    print('Downloading: ' + download_url)
    urllib.request.urlretrieve(download_url, filename)

    if args.upload:
      upload_url = upload_base + filename
      print('Uploading: ' + upload_url)
      cmd = ['gsutil', 'cp', '-n', filename, upload_url]
      print(' '.join(cmd))
      subprocess.check_call(cmd)
      os.remove(filename)


if __name__ == '__main__':
  main()
