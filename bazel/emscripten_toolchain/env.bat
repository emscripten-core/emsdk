@ECHO OFF

set ROOT_DIR=%EXT_BUILD_ROOT%
if "%ROOT_DIR%"=="" set ROOT_DIR=%CD%
set EMSCRIPTEN=%ROOT_DIR%\%EM_BIN_PATH%\emscripten
set EM_CONFIG=%ROOT_DIR%\%EM_CONFIG_PATH%

:: If EMSDK_PYTHON is a relative path, make it absolute using ROOT_DIR.
:: This is needed because emscripten system library generation invokes compilers
:: from subdirectories inside its cache, where relative paths to python break.
if not "%EMSDK_PYTHON%"=="" ^
if not "%EMSDK_PYTHON:~1,1%"==":" ^
if not "%EMSDK_PYTHON:~0,1%"=="\" ^
	set "EMSDK_PYTHON=%ROOT_DIR%\%EMSDK_PYTHON%"
