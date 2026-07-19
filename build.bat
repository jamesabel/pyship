rmdir /S /Q dist
rmdir /S /Q build
call venv\scripts\activate.bat
python -m build --wheel
if errorlevel 1 (
    echo build failed
    call deactivate
    exit /b 1
)
call deactivate
