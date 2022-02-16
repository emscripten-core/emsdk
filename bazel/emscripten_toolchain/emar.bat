@ECHO OFF

call external\emsdk\emscripten_toolchain\env.bat

py -3 %EMSCRIPTEN%\emar.py %*
