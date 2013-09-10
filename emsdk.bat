@echo off

:: Find python from an explicit location relative to the Emscripten SDK.
IF EXIST "%~dp0python\2.7.5.1_32bit\python.exe" (
  call "%~dp0python\2.7.5.1_32bit\python" "%~dp0\emsdk" %*
  GOTO end
)

:: As last resort, access from PATH.
call python "%~dp0\emsdk" %*
GOTO end

:end
@echo on
