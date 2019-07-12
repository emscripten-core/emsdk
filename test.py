import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

# Utilities

def listify(x):
  if type(x) == list or type(x) == tuple:
    return x
  return [x]

def check_call(cmd):
  subprocess.check_call(shlex.split(cmd))

def checked_call_with_output(cmd, expected=None, unexpected=None, stderr=None):
  stdout = subprocess.check_output(cmd.split(' '), stderr=stderr)
  if expected:
    for x in listify(expected):
      assert x in stdout, 'call had the right output: ' + stdout + '\n[[[' + x + ']]]'
  if unexpected:
    for x in listify(unexpected):
      assert x not in stdout, 'call had the wrong output: ' + stdout + '\n[[[' + x + ']]]'

def failing_call_with_output(cmd, expected):
  proc = subprocess.Popen(cmd.split(' '), stdout=subprocess.PIPE)
  stdout, stderr = proc.communicate()
  assert proc.returncode, 'call must have failed'
  assert expected in stdout, 'call did not have the right output'

def hack_emsdk(marker, replacement):
  src = open('emsdk').read()
  assert marker in src
  src = src.replace(marker, replacement)
  name = '__test_emsdk'
  open(name, 'w').write(src)
  return name

# Set up

open('hello_world.cpp', 'w').write('int main() {}')

TAGS = json.loads(open('emscripten-releases-tags.txt').read())

LIBC = os.path.expanduser('~/.emscripten_cache/wasm-obj/libc.a')

# Tests

print('test .emscripten contents (latest was installed/activated in test.sh)')
assert 'fastcomp' in open(os.path.expanduser('~/.emscripten')).read()
assert 'upstream' not in open(os.path.expanduser('~/.emscripten')).read()

print('building proper system libraries')

def test_lib_building(prefix, use_asmjs_optimizer):
  def test_build(args, expected=None, unexpected=None):
    checked_call_with_output(prefix + '/emscripten/emcc hello_world.cpp' + args,
                             expected=expected,
                             unexpected=unexpected,
                             stderr=subprocess.STDOUT)

  # by default we ship libc, struct_info, and the asm.js optimizer, as they
  # are important for various reasons (libc takes a long time to build;
  # struct_info is a bootstrap product so if the user's setup is broken it's
  # confusing; the asm.js optimizer is a native application so it needs a
  # working native local build environment). otherwise we don't ship every
  # single lib, so some building is expected on first run.

  unexpected_system_libs = ['generating system library: libc.',
                            'generating system asset: optimizer']
  if use_asmjs_optimizer:
    unexpected_system_libs += ['generating system asset: generated_struct_info.json']

  first_time_system_libs = ['generating system library: libdlmalloc.']

  test_build('', expected=first_time_system_libs,
                 unexpected=unexpected_system_libs)
  test_build(' -O2', unexpected=unexpected_system_libs + first_time_system_libs)
  test_build(' -s WASM=0', unexpected=unexpected_system_libs + first_time_system_libs)
  test_build(' -O2 -s WASM=0', unexpected=unexpected_system_libs + first_time_system_libs)

test_lib_building('fastcomp', use_asmjs_optimizer=True)

print('update')
check_call('./emsdk update-tags')

print('test latest-releases-upstream')
check_call('python2 ./emsdk install latest-upstream')
check_call('./emsdk activate latest-upstream')
test_lib_building('upstream', use_asmjs_optimizer=False)
assert open(os.path.expanduser('~/.emscripten')).read().count('LLVM_ROOT') == 1
assert 'upstream' in open(os.path.expanduser('~/.emscripten')).read()
assert 'fastcomp' not in open(os.path.expanduser('~/.emscripten')).read()

print('verify version')
checked_call_with_output('upstream/emscripten/emcc -v', TAGS['latest'], stderr=subprocess.STDOUT)

print('clear cache')
check_call('upstream/emscripten/emcc --clear-cache')
assert not os.path.exists(LIBC)

print('test tot-upstream')
check_call('./emsdk install tot-upstream')
assert not os.path.exists(LIBC)
old_config = open(os.path.expanduser('~/.emscripten')).read()
check_call('./emsdk activate tot-upstream')
assert old_config == open(os.path.expanduser('~/.emscripten.old')).read()
assert os.path.exists(LIBC), 'activation supplies prebuilt libc' # TODO; test on latest as well
check_call('upstream/emscripten/emcc hello_world.cpp')

print('test tot-fastcomp')
check_call('./emsdk install tot-fastcomp')
check_call('./emsdk activate tot-fastcomp')
check_call('fastcomp/emscripten/emcc hello_world.cpp')

print('test specific release (old)')
check_call('./emsdk install sdk-1.38.31-64bit')
check_call('./emsdk activate sdk-1.38.31-64bit')

print('test specific release (new, short name)')
check_call('./emsdk install 1.38.33')
check_call('./emsdk activate 1.38.33')
assert 'fastcomp' in open(os.path.expanduser('~/.emscripten')).read()
assert 'upstream' not in open(os.path.expanduser('~/.emscripten')).read()

print('test specific release (new, full name)')
check_call('./emsdk install sdk-1.38.33-upstream-64bit')
check_call('./emsdk activate sdk-1.38.33-upstream-64bit')

print('test specific release (new, full name)')
check_call('./emsdk install sdk-tag-1.38.33-64bit')
check_call('./emsdk activate sdk-tag-1.38.33-64bit')

print('test binaryen source build')
check_call('./emsdk install --build=Release --generator="Unix Makefiles" binaryen-master-64bit')

print('test 32-bit error')

failing_call_with_output('python %s install latest' % hack_emsdk('not is_os_64bit()', 'True'), 'this tool is only provided for 64-bit OSes')

print('test non-git update')

temp_dir = tempfile.mkdtemp()

for filename in os.listdir('.'):
  if not filename.startswith('.') and not os.path.isdir(filename):
    shutil.copyfile(filename, os.path.join(temp_dir, filename))

os.chdir(temp_dir)

check_call('python ./emsdk update')
print('second time')
check_call('python ./emsdk update')

print('verify downloads exist for all OSes')
latest_hash = TAGS['releases'][TAGS['latest']]
for os, suffix in [
  ('linux', 'tbz2'),
  ('mac', 'tbz2'),
  ('win', 'zip')
]:
  url = 'https://storage.googleapis.com/webassembly/emscripten-releases-builds/%s/%s/wasm-binaries.%s' % (os, latest_hash, suffix)
  print('  url: ' + url),
  check_call('wget ' + url)
