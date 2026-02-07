pushd .
cd ..
call build.bat
call venv\scripts\activate.bat
call twine upload dist\*
call deactivate
popd
