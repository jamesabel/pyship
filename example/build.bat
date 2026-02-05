@echo on
rmdir /S /Q dist
rmdir /S /Q build
call venv\Scripts\activate.bat
python -m build --wheel
deactivate
