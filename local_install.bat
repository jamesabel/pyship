REM install latest pyship into the venvs
REM
REM pyships's venv
venv\Scripts\python setup.py bdist_wheel
venv\Scripts\pip.exe uninstall -y pyship
venv\Scripts\pip.exe install pyship --no-index -f dist
REM
REM test case venvs
cd test_pyship\tstpyshipapp_0.0.1
venv\Scripts\pip.exe uninstall -y pyship
venv\Scripts\pip.exe install pyship --no-index -f ..\..\dist
rmdir /S /Q dist
rmdir /S /Q build
venv\Scripts\python.exe setup.py bdist_wheel
REM
cd ..\tstpyshipapp_0.0.2
venv\Scripts\pip.exe uninstall -y pyship
venv\Scripts\pip.exe install pyship --no-index -f ..\..\dist
rmdir /S /Q dist
rmdir /S /Q build
venv\Scripts\python.exe setup.py bdist_wheel
cd ..\..
