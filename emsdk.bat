@SET PREVPATH=%PATH%

:: Find python from an explicit location relative to the Emscripten SDK.
@IF EXIST "%~dp0python\2.7.5.3_64bit\python.exe" (
  @SET EMSDK_PY=%~dp0python\2.7.5.3_64bit\python.exe
  @GOTO end
)

@IF EXIST "%~dp0python\2.7.5.3_32bit\python.exe" (
  @SET EMSDK_PY=%~dp0python\2.7.5.3_32bit\python.exe
  @GOTO end
)

@IF EXIST "%~dp0python\2.7.5_64bit\python.exe" (
  @SET EMSDK_PY=%~dp0python\2.7.5_64bit\python.exe
  @GOTO end
)

@IF EXIST "%~dp0python\2.7.5.1_32bit\python.exe" (
  @SET EMSDK_PY=%~dp0python\2.7.5.1_32bit\python.exe
  @GOTO end
)

:: As last resort, access from PATH.
@SET EMSDK_PY=python

:end
@call %EMSDK_PY% "%~dp0\emsdk" %*

@set EMSDK_PY=
@set PATH=%PREVPATH%
@set PREVPATH=
