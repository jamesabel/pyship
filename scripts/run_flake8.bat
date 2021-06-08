pushd .
cd ..
del doc\flake8_report.txt
call venv\Scripts\activate.bat
REM
REM E402 module level import not at top of file
REM F401 imported but unused
REM W503 line break before binary operator (black puts this in)
REM E203 whitespace before ':' (black puts this in and may be controversial)
REM E501 line too long
flake8 --output-file doc\flake8_report.txt --ignore=E402,F401,W503,E203,E501 --exclude app,build,cache,dist,installers,venv --tee pyship test_pyship
call deactivate
popd
