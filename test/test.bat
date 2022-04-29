:: equivilent of test.sh as windows bat file
set PATH=%PATH%;%PYTHON_BIN%
CALL emsdkpy/emsdk install latest
CALL emsdkpy/emsdk activate latest
CALL emsdkpy/emsdk_env.bat
CALL python -c "import sys; print(sys.executable)"
CALL emcc.bat -v
