rmdir /S /Q dist
call venv\scripts\activate.bat
python setup.py bdist_wheel
REM twine upload -r testpypi dist\*
deactivate
