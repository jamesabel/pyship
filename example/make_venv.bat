@echo on

REM Build pyship from local source if available (so we get the latest even if not on PyPI)
if exist ..\pyproject.toml (
    if exist ..\venv\Scripts\python.exe (
        echo Building pyship wheel from local source ...
        rmdir /S /Q ..\dist 2>nul
        rmdir /S /Q ..\build 2>nul
        ..\venv\Scripts\python.exe -m build --wheel ..\
    ) else (
        echo WARNING: parent pyship venv not found, skipping local build
    )
)

rmdir /S /Q venv
"C:\Program Files\Python314\python.exe" -m venv --clear venv
venv\Scripts\python.exe -m pip install --upgrade pip
venv\Scripts\pip3.exe install -U setuptools
venv\Scripts\pip3.exe install -U -r requirements.txt -f ..\dist
