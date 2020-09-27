rmdir /S /Q dist
rmdir /S /Q build
call venv\scripts\activate.bat
python setup.py bdist_wheel
deactivate
