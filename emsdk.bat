:: Find python from an explicit location relative to the Emscripten SDK.
@IF EXIST "%~dp0python\2.7.13.1_64bit\python-2.7.13.amd64\python.exe" (
  @SET EMSDK_PY="%~dp0python\2.7.13.1_64bit\python-2.7.13.amd64\python.exe"
  @GOTO end
)

@IF EXIST "%~dp0python\2.7.13.1_32bit\python-2.7.13\python.exe" (
  @SET EMSDK_PY="%~dp0python\2.7.13.1_32bit\python-2.7.13\python.exe"
  @GOTO end
)

@IF EXIST "%~dp0python\2.7.5.3_64bit\python.exe" (
  @SET EMSDK_PY="%~dp0python\2.7.5.3_64bit\python.exe"
  @GOTO end
)

@IF EXIST "%~dp0python\2.7.5.3_32bit\python.exe" (
  @SET EMSDK_PY="%~dp0python\2.7.5.3_32bit\python.exe"
  @GOTO end
)

@IF EXIST "%~dp0python\2.7.5_64bit\python.exe" (
  @SET EMSDK_PY="%~dp0python\2.7.5_64bit\python.exe"
  @GOTO end
)

@IF EXIST "%~dp0python\2.7.5.1_32bit\python.exe" (
  @SET EMSDK_PY="%~dp0python\2.7.5.1_32bit\python.exe"
  @GOTO end
)

:: As a last resort, access from PATH.
@SET EMSDK_PY=python

:end
@call %EMSDK_PY% "%~dp0\emsdk" %*

@set EMSDK_PY=

:: python is not able to set environment variables to the parent calling process, so
:: therefore have it craft a .bat file, which we invoke after finishing python execution,
:: to set up the environment variables
@IF EXIST emsdk_set_env.bat (
  @CALL emsdk_set_env.bat > NUL
  @DEL /F /Q emsdk_set_env.bat
)
