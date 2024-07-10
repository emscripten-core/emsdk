@ECHO OFF

set ROOT_DIR=%CD%
set EMSCRIPTEN=%ROOT_DIR%\%EM_BIN_PATH%\emscripten
set EM_CONFIG=%ROOT_DIR%\%EM_CONFIG_PATH%

:: Ensure PYTHONSAFEPATH is not set so that modules in the same
:: directory as emcc.py and emar.py etc. can be found via sys.path
set PYTHONSAFEPATH=
