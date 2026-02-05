pushd .
cd ..
REM make pyship the app
call local_install.bat
venv\Scripts\python.exe -m pyship -p bup
pushd
