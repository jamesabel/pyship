pushd .
cd ..
call build.bat
if errorlevel 1 (
    echo build failed - aborting PyPI upload
    popd
    exit /b 1
)
if not exist dist\*.whl (
    echo no wheel in dist - aborting PyPI upload
    popd
    exit /b 1
)
call venv\scripts\activate.bat
call twine upload dist\*
if errorlevel 1 (
    echo twine upload failed
    call deactivate
    popd
    exit /b 1
)
call deactivate
popd
