call build.bat
call venv\scripts\activate.bat
twine upload -r testpypi dist\*
deactivate
