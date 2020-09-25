REM make pyship the app
call local_install.bat
venv\Scripts\pytest.exe --rootdir="." -s test_pyship
