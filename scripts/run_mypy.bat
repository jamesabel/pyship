pushd .
cd ..
call venv\Scripts\activate.bat 
mypy -m pyship
mypy -m test_pyship
call deactivate
popd
