::This script looks up the set of currently activated emscripten tools, and adds all the necessary directories for each of them to PATH for the current command shell.
@echo off

@call "%~dp0emsdk" active_path > nul 2> nul
if ERRORLEVEL 1 goto error
set ACTIVE_PATH=
FOR /F "tokens=*" %%i in ('"%~dp0emsdk" active_path') do SET ACTIVE_PATH=%%i
SET PATH=%ACTIVE_PATH%;%PATH%

::echo.
::IF "%ACTIVE_PATH%" == "" (
::echo No items needed to be added to PATH. Emscripten SDK is all set!
::) ELSE (
echo The following directories have been added to PATH:
echo.
echo PATH += %ACTIVE_PATH%
::)

SET ACTIVE_PATH=
goto end

:error
echo Error: Cannot add tools to path: no active SDK detected! Activate an SDK first by typing 'emsdk activate [tool/sdk name]'.
echo.

:end
