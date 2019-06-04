import os
import subprocess
import sys

# Utilities

def check_call(cmd):
  subprocess.check_call(cmd.split(' '))

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

print('test binaryen source build')
check_call('./emsdk install --build=Release binaryen-master-64bit')

print('test 32-bit error')

failing_call_with_output('python %s install latest' % hack_emsdk('not is_os_64bit()', 'True'), 'this tool is only provided for 64-bit OSes')

