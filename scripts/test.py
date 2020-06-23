#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
import sys
import tempfile

WINDOWS = sys.platform.startswith('win')
MACOS = sys.platform == 'darwin'

assert 'EM_CONFIG' in os.environ, "emsdk should be activated before running this script"

LIBC = os.environ['EM_CACHE'] + '/wasm/libc.a'

# Remove the EM_CACHE environment variable.  It interferes with testing since
# it would otherwise be fixed for the duration of the script and we expect
# "emsdk activate" to be able switch between SDKs during the running of this
# script.
del os.environ['EM_CACHE']

emconfig = os.environ['EM_CONFIG']
upstream_emcc = os.path.join('upstream', 'emscripten', 'emcc')
fastcomp_emcc = os.path.join('fastcomp', 'emscripten', 'emcc')
emsdk = './emsdk'
if WINDOWS:
  upstream_emcc += '.bat'
  fastcomp_emcc += '.bat'
  emsdk = 'emsdk.bat'
else:
  emsdk = './emsdk'

# Utilities


def listify(x):
  if type(x) == list or type(x) == tuple:
    return x
  return [x]


def check_call(cmd, **args):
  if type(cmd) != list:
    cmd = cmd.split()
  print('running: %s' % cmd)
  args['universal_newlines'] = True
  subprocess.check_call(cmd, **args)


def checked_call_with_output(cmd, expected=None, unexpected=None, stderr=None):
  cmd = cmd.split(' ')
  print('running: %s' % cmd)
  stdout = subprocess.check_output(cmd, stderr=stderr, universal_newlines=True)
  if expected:
    for x in listify(expected):
      assert x in stdout, 'call had the right output: ' + stdout + '\n[[[' + x + ']]]'
  if unexpected:
    for x in listify(unexpected):
      assert x not in stdout, 'call had the wrong output: ' + stdout + '\n[[[' + x + ']]]'


def failing_call_with_output(cmd, expected):
  proc = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE, universal_newlines=True)
  stdout, stderr = proc.communicate()
  assert proc.returncode, 'call must have failed'
  assert expected in stdout, 'call did not have the right output'


def hack_emsdk(marker, replacement):
  src = open('emsdk.py').read()
  assert marker in src
  src = src.replace(marker, replacement)
  name = '__test_emsdk'
  open(name, 'w').write(src)
  return name


# Set up

open('hello_world.c', 'w').write('''\
#include <stdio.h>

int main() {
   printf("Hello, world!\\n");
   return 0;
}
''')

TAGS = json.loads(open('emscripten-releases-tags.txt').read())

# Tests

print('test .emscripten contents (latest was installed/activated in test.sh)')
assert 'fastcomp' not in open(emconfig).read()
assert 'upstream' in open(emconfig).read()

# Test we don't re-download unnecessarily
checked_call_with_output(emsdk + ' install latest', expected='already installed', unexpected='Downloading:')

# Test we report installed tools properly. The latest version should be
# installed, but not some random old one.
checked_call_with_output(emsdk + ' list', expected=TAGS['latest'] + '    INSTALLED', unexpected='1.39.15    INSTALLED:')

print('building proper system libraries')


def test_lib_building(emcc, use_asmjs_optimizer):
  cache_building_messages = ['generating system library: ']

  def test_build(args, expected):
    if expected:
      expected = cache_building_messages
      unexpected = []
    else:
      expected = []
      unexpected = cache_building_messages
    checked_call_with_output(emcc + ' hello_world.c' + args,
                             expected=expected,
                             unexpected=unexpected,
                             stderr=subprocess.STDOUT)

  # The emsdk ships all system libraries so we don't expect to see any
  # cache population unless we explicly --clear-cache.
  test_build('', expected=False)
  check_call(emcc + ' --clear-cache')
  test_build(' -O2', expected=True)
  test_build(' -s WASM=0', expected=False)
  test_build(' -O2 -s WASM=0', expected=False)


def run_emsdk(cmd):
  if type(cmd) != list:
    cmd = cmd.split()
  check_call([emsdk] + cmd)


test_lib_building(upstream_emcc, use_asmjs_optimizer=True)

print('update')
run_emsdk('update-tags')

print('test latest-releases-fastcomp')
run_emsdk('install latest-fastcomp')
run_emsdk('activate latest-fastcomp')

test_lib_building(fastcomp_emcc, use_asmjs_optimizer=False)
assert open(emconfig).read().count('LLVM_ROOT') == 1
assert 'upstream' not in open(emconfig).read()
assert 'fastcomp' in open(emconfig).read()

print('verify version')
checked_call_with_output(fastcomp_emcc + ' -v', TAGS['latest'], stderr=subprocess.STDOUT)

print('clear cache')
check_call(upstream_emcc + ' --clear-cache')
assert not os.path.exists(LIBC)

# Test the normal tools like node don't re-download on re-install
print('another install must re-download')
checked_call_with_output(emsdk + ' uninstall node-12.18.1-64bit')
checked_call_with_output(emsdk + ' install node-12.18.1-64bit', expected='Downloading:', unexpected='already installed')
checked_call_with_output(emsdk + ' install node-12.18.1-64bit', unexpected='Downloading:', expected='already installed')

print('test tot-upstream')
run_emsdk('install tot-upstream')
old_config = open(emconfig).read()
run_emsdk('activate tot-upstream')
assert old_config == open(emconfig + '.old').read()
# TODO; test on latest as well
check_call(upstream_emcc + ' hello_world.c')

print('test tot-fastcomp')
run_emsdk('install tot-fastcomp')
run_emsdk('activate tot-fastcomp')
check_call(fastcomp_emcc + ' hello_world.c')

print('test specific release (old)')
run_emsdk('install sdk-fastcomp-1.38.31-64bit')
run_emsdk('activate sdk-fastcomp-1.38.31-64bit')

print('test specific release (new, short name)')
run_emsdk('install 1.38.33')
print('another install, but no need for re-download')
checked_call_with_output(emsdk + ' install 1.38.33', expected='Skipped', unexpected='Downloading:')
run_emsdk('activate 1.38.33')
assert 'upstream' not in open(emconfig).read()
assert 'fastcomp' in open(emconfig).read()

print('test specific release (new, full name)')
run_emsdk('install sdk-1.38.33-upstream-64bit')
run_emsdk('activate sdk-1.38.33-upstream-64bit')

print('test specific release (new, full name)')
run_emsdk('install sdk-tag-1.38.33-64bit')
run_emsdk('activate sdk-tag-1.38.33-64bit')

print('test binaryen source build')
run_emsdk(['install', '--build=Release', '--generator=Unix Makefiles', 'binaryen-master-64bit'])

print('test 32-bit error')

failing_call_with_output('python %s install latest' % hack_emsdk('not is_os_64bit()', 'True'), 'this tool is only provided for 64-bit OSes')

print('test non-git update')

temp_dir = tempfile.mkdtemp()

for filename in os.listdir('.'):
  if not filename.startswith('.') and not os.path.isdir(filename):
    shutil.copy2(filename, os.path.join(temp_dir, filename))

os.chdir(temp_dir)

run_emsdk('update')
print('second time')
run_emsdk('update')

print('verify downloads exist for all OSes')
latest_hash = TAGS['releases'][TAGS['latest']]
for osname, suffix in [
  ('linux', 'tbz2'),
  ('mac', 'tbz2'),
  ('win', 'zip')
]:
  url = 'https://storage.googleapis.com/webassembly/emscripten-releases-builds/%s/%s/wasm-binaries.%s' % (osname, latest_hash, suffix)
  print('  checking url: ' + url),
  check_call('curl --fail --head --silent ' + url, stdout=subprocess.PIPE)
