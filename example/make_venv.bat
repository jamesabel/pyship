@echo on
rmdir /S /Q venv
python -m venv --clear venv
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\pip3.exe install -U setuptools
venv\Scripts\pip3.exe install -U -r requirements.txt -f ..\dist
