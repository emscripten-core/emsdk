@echo off
setlocal

set _args=%*
if "%~1"=="-?" set _args=-help

powershell -ExecutionPolicy ByPass -NoProfile -File "%~dp0eng\common\build.ps1" -restore -build -pack %_args%
exit /b %ERRORLEVEL%
