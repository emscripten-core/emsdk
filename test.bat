:: equivilent of test.sh as windows bat file
set PATH=%PATH%;%PYTHON_BIN%
@CALL emsdk install latest
@CALL emsdk activate latest
@CALL emsdk_env.bat --build=Release
@CALL emcc.bat -v
