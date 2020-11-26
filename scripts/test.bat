:: equivilent of test.sh as windows bat file
set PATH=%PATH%;%PYTHON_BIN%
set OLD_PATH=%PATH%
CALL emsdk install latest

:: first test with --persistent
CALL emsdk activate latest
CALL emsdk_env.bat --persistent
:: Check that no path elements were removed
CALL python scripts/check_path.py "%OLD_PATH%"
CALL python -c "import sys; print(sys.executable)"
CALL emcc.bat -v

:: then test without --persistent
CALL emsdk activate latest
CALL emsdk_env.bat
:: Check that no path elements were removed
CALL python scripts/check_path.py "%OLD_PATH%"
CALL python -c "import sys; print(sys.executable)"
CALL emcc.bat -v
