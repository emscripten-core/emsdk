#!/usr/bin/env python3
# Copyright 2019 The Emscripten Authors.  All rights reserved.
# Emscripten is available under two separate licenses, the MIT license and the
# University of Illinois/NCSA Open Source License.  Both these licenses can be
# found in the LICENSE file.

# The very beginnings of some unit tests for emsdk.  Hopefully this grow over
# time.

import os
import tempfile
import time
import unittest

import emsdk


def count_files(dirname):
  listing = os.listdir(dirname)
  return len([f for f in listing if os.path.isfile(os.path.join(dirname, f))])


class TestDownloadCache(unittest.TestCase):
  def setUp(self):
    self.tmpdir = tempfile.TemporaryDirectory('test_emsdk')
    emsdk.zips_subdir = self.tmpdir.name
    emsdk.VERBOSE = True
    print(emsdk.zips_subdir)

  def tearDown(self):
    self.tmpdir.cleanup()

  def test_limits(self):
    for n in range(emsdk.CACHE_MAX_FILES + 1):
      with open(os.path.join(emsdk.zips_subdir, 'tmp%s' % n), 'w') as f:
        f.write('foo')
    self.assertEqual(count_files(emsdk.zips_subdir), emsdk.CACHE_MAX_FILES + 1)
    emsdk.cleanup_downloads()
    self.assertEqual(count_files(emsdk.zips_subdir), emsdk.CACHE_MAX_FILES)

  def test_age(self):
    for n in range(emsdk.CACHE_MAX_FILES + 10):
      with open(os.path.join(emsdk.zips_subdir, 'tmp%s' % n), 'w') as f:
        f.write('foo')

    # Make sure tmp5 is the oldest file.
    t = time.time() - 60
    os.utime(os.path.join(emsdk.zips_subdir, 'tmp5'), (t, t))
    emsdk.cleanup_downloads()

    # Ensure tmp5 was among those purged
    self.assertIn('tmp1', os.listdir(emsdk.zips_subdir))
    self.assertNotIn('tmp5', os.listdir(emsdk.zips_subdir))


if __name__ == '__main__':
  unittest.main()
