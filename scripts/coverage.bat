pushd .
cd ..
set PYTHONPATH=%CD%
venv\Scripts\python.exe -m pytest --cov-report=html --cov
popd
