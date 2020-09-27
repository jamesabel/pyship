REM download all external packages from pypi and copy them locally
echo on
pushd .
cd ..
call venv\Scripts\activate.bat
echo on
mkdir pip_download
IF NOT "%PYPILOCAL%"=="" (pip download -r requirements-dev.txt -d %PYPILOCAL%)
popd
deactivate
