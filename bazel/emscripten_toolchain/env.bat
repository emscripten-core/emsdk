@ECHO OFF

set ROOT_DIR=%EXT_BUILD_ROOT%
if "%ROOT_DIR%"=="" set ROOT_DIR=%CD%
set EMSCRIPTEN=%ROOT_DIR%\%EM_BIN_PATH%\emscripten
set EM_CONFIG=%ROOT_DIR%\%EM_CONFIG_PATH%
set EMSDK_PYTHON=%ROOT_DIR%\%BAZEL_PYTHON_RELPATH%

REM See env.sh: keep emscripten's Python imports inside the sandbox.
set PYTHONSAFEPATH=1
set PYTHONPATH=%EMSCRIPTEN%
