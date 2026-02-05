rmdir /S /Q dist
rmdir /S /Q build
call venv\scripts\activate.bat
python -m build --wheel
deactivate
