pushd .
cd ..
rmdir /S /Q venv
uv venv venv
uv pip install --python venv\Scripts\python.exe -U setuptools
uv pip install --python venv\Scripts\python.exe -U -r requirements-dev.txt
popd
