import json
import os
import shutil
import subprocess
import sys
import tempfile

# Utilities

def check_call(cmd):
  subprocess.check_call(cmd.split(' '))

def checked_call_with_output(cmd, expected, stderr=None):
  stdout = subprocess.check_output(cmd.split(' '), stderr=stderr)
  assert expected in stdout, 'call did not have the right output: ' + stdout

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

# Tests

print('update')
check_call('./emsdk update-tags')

print('test latest')
assert 'fastcomp' in open(os.path.expanduser('~/.emscripten')).read()
assert 'upstream' not in open(os.path.expanduser('~/.emscripten')).read()

print('test latest-releases-upstream')
check_call('python2 ./emsdk install latest-upstream')
check_call('./emsdk activate latest-upstream')
check_call('upstream/emscripten/emcc hello_world.cpp')
assert open(os.path.expanduser('~/.emscripten')).read().count('LLVM_ROOT') == 1
assert 'upstream' in open(os.path.expanduser('~/.emscripten')).read()
assert 'fastcomp' not in open(os.path.expanduser('~/.emscripten')).read()

print('verify version')
checked_call_with_output('upstream/emscripten/emcc -v', TAGS['latest'], stderr=subprocess.STDOUT)

print('test tot-upstream')
check_call('./emsdk install tot-upstream')
check_call('./emsdk activate tot-upstream')
check_call('upstream/emscripten/emcc hello_world.cpp')

print('test tot-fastcomp')
check_call('./emsdk install tot-fastcomp')
check_call('./emsdk activate tot-fastcomp')
check_call('fastcomp/emscripten/emcc hello_world.cpp')

print('test specific release (old)')
check_call('./emsdk install sdk-1.38.31-64bit')
check_call('./emsdk activate tot-fastcomp')

print('test specific release (new, short name)')
check_call('./emsdk install 1.38.33')
check_call('./emsdk activate tot-fastcomp')
assert 'fastcomp' in open(os.path.expanduser('~/.emscripten')).read()
assert 'upstream' not in open(os.path.expanduser('~/.emscripten')).read()

print('test specific release (new, full name)')
check_call('./emsdk install sdk-1.38.33-upstream-64bit')
check_call('./emsdk activate sdk-1.38.33-upstream-64bit')

print('test specific release (new, full name)')
check_call('./emsdk install sdk-tag-1.38.33-64bit')
check_call('./emsdk activate sdk-tag-1.38.33-64bit')

print('test binaryen source build')
check_call('./emsdk install --build=Release binaryen-master-64bit')

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

