echo on
rmdir /S /Q venv
"\Program Files\Python38\python.exe" -m venv --clear venv
venv\Scripts\python.exe -m pip install --no-deps --upgrade pip
venv\Scripts\pip3 install -U setuptools
venv\Scripts\pip3 install -U -r requirements-dev.txt -f ..\pyshipupdate\dist
