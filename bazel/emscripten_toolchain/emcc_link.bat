@ECHO OFF

call external\emsdk\emscripten_toolchain\env.bat

%EMSDK_PYTHON% external\emsdk\emscripten_toolchain\link_wrapper.py %*
