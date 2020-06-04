:: equivilent of test.sh as windows bat file
set PATH=%PATH%;%PYTHON_BIN%
@CALL emsdk install tot
@CALL emsdk activate tot
@CALL emsdk_env.bat --build=Release
@CALL python -c "import sys; print(sys.executable)"
set EMCC_DEBUG=1
@CALL emcc.bat -v
