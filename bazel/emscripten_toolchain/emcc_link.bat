@ECHO OFF

call %~dp0\env.bat

"%EMSDK_PYTHON%" %~dp0\link_wrapper.py %*
