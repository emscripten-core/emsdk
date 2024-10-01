@ECHO OFF

call external\emsdk\emscripten_toolchain\env.bat

%EMSDK_PYTHON% %EMSCRIPTEN%\emar.py %*
