@ECHO OFF

call %~dp0\env.bat

"%EMSDK_PYTHON%" %EMSCRIPTEN%\emcc.py %*
