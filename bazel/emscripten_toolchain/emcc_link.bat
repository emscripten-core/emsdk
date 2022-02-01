@ECHO OFF

call external\emsdk\emscripten_toolchain\env.bat

py -3 external\emsdk\emscripten_toolchain\link_wrapper.py %*
