@echo off

:: Find python from an explicit location relative to the Emscripten SDK.

setlocal

if exist "%~dp0python\3.7.4-pywin32_64bit\python.exe" (
  set EMSDK_PY="%~dp0python\3.7.4-pywin32_64bit\python.exe"
  goto end
)

if exist "%~dp0python\3.7.4_64bit\python.exe" (
  set EMSDK_PY="%~dp0python\3.7.4_64bit\python.exe"
  goto end
)

if exist "%~dp0python\2.7.13.1_64bit\python-2.7.13.amd64\python.exe" (
  set EMSDK_PY="%~dp0python\2.7.13.1_64bit\python-2.7.13.amd64\python.exe"
  goto end
)

if exist "%~dp0python\2.7.13.1_32bit\python-2.7.13\python.exe" (
  set EMSDK_PY="%~dp0python\2.7.13.1_32bit\python-2.7.13\python.exe"
  goto end
)

if exist "%~dp0python\2.7.5.3_64bit\python.exe" (
  set EMSDK_PY="%~dp0python\2.7.5.3_64bit\python.exe"
  goto end
)

if exist "%~dp0python\2.7.5.3_32bit\python.exe" (
  set EMSDK_PY="%~dp0python\2.7.5.3_32bit\python.exe"
  goto end
)

if exist "%~dp0python\2.7.5_64bit\python.exe" (
  set EMSDK_PY="%~dp0python\2.7.5_64bit\python.exe"
  goto end
)

if exist "%~dp0python\2.7.5.1_32bit\python.exe" (
  set EMSDK_PY="%~dp0python\2.7.5.1_32bit\python.exe"
  goto end
)

:: As a last resort, access from PATH.
set EMSDK_PY=python

:end
call %EMSDK_PY% "%~dp0\emsdk.py" %*

endlocal

:: python is not able to set environment variables to the parent calling
:: process, so therefore have it craft a .bat file, which we invoke after
:: finishing python execution, to set up the environment variables
if exist "%~dp0\emsdk_set_env.bat" (
  call "%~dp0\emsdk_set_env.bat" > nul
  del /F /Q "%~dp0\emsdk_set_env.bat"
)
