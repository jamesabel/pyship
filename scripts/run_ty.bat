@echo off
pushd .
cd ..
call venv\Scripts\activate.bat
ty check pyship
call deactivate
popd
