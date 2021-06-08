pushd .
cd ..
call venv\Scripts\activate.bat 
mypy -m pyship
call deactivate
popd
