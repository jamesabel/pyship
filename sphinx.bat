set PYTHONPATH=%CD%
call venv\Scripts\activate
pushd .
cd docs
call make.bat html
popd
call venv\Scripts\deactivate
copy /Y docs\source\readme.rst readme.rst
