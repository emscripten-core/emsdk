:: equivilent of test.sh as windows bat file
set PATH=%PATH%;%PYTHON_BIN%
set OLD_PATH=%PATH%
@CALL emsdk install latest
@CALL emsdk activate latest
@CALL emsdk_env.bat --build=Release
@CALL python -c "import sys; print(sys.executable)"
@CALL emcc.bat -v
:: Check that no path elements were removed
@CALL python scripts/check_path.py "%OLD_PATH%"
