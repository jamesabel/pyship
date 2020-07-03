call build.bat
call venv\scripts\activate.bat
REM twine upload -r testpypi dist\*
deactivate
