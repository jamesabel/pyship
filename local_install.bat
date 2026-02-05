REM install latest pyship into the venvs
REM
REM first update pyshipupdate
cd ..\pyshipupdate
call build.bat
cd ..\pyship
REM
REM pyships's venv
call make_venv.bat
rmdir /S /Q dist
rmdir /S /Q build
venv\Scripts\python -m build --wheel
venv\Scripts\pip.exe uninstall -y pyship
venv\Scripts\pip.exe install pyship -f dist
venv\Scripts\pip.exe uninstall -y pyshipupdate
venv\Scripts\pip.exe install pyshipupdate -f ..\pyshipupdate\dist
REM
REM test case venvs
cd test_pyship\tstpyshipapp_0.0.1
call make_venv.bat
venv\Scripts\pip.exe uninstall -y pyship
venv\Scripts\pip.exe install pyship -f ..\..\dist
venv\Scripts\pip.exe uninstall -y pyshipupdate
venv\Scripts\pip.exe install pyshipupdate -f ..\..\..\pyshipupdate\dist
rmdir /S /Q dist
rmdir /S /Q build
venv\Scripts\python.exe setup.py bdist_wheel
REM
cd ..\tstpyshipapp_0.0.2
call make_venv.bat
venv\Scripts\pip.exe uninstall -y pyship
venv\Scripts\pip.exe install pyship -f ..\..\dist
venv\Scripts\pip.exe uninstall -y pyshipupdate
venv\Scripts\pip.exe install pyshipupdate -f ..\..\..\pyshipupdate\dist
rmdir /S /Q dist
rmdir /S /Q build
venv\Scripts\python.exe setup.py bdist_wheel
cd ..\..
