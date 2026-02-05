@echo off
pushd .
cd ..
echo Running ruff check...
venv\Scripts\ruff.exe check pyship test_pyship
echo.
echo Running ruff format check...
venv\Scripts\ruff.exe format --check pyship test_pyship
popd
