:: Make sure changes to PATH are not propagated to the calling shell
setlocal

:: Find python from an explicit location relative to the Emscripten SDK.
@SET PATH=%~dp0python\2.7.5.3_64bit\;%~dp0python\2.7.5.3_32bit\;%~dp0python\2.7.5_64bit\;%~dp0python\2.7.5.1_32bit\;%PATH%
@call python.exe "%~dp0\emsdk" %*

endlocal

:: python is not able to set environment variables to the parent calling process, so
:: therefore have it craft a .bat file, which we invoke after finishing python execution,
:: to set up the environment variables
@IF EXIST emsdk_set_env.bat (
  @CALL emsdk_set_env.bat > NUL
  @DEL /F /Q emsdk_set_env.bat
)
