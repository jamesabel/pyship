@echo off
pushd .
cd ..
echo Running ruff check with --fix...
venv\Scripts\ruff.exe check --fix pyship test_pyship
echo.
echo Running ruff format...
venv\Scripts\ruff.exe format pyship test_pyship
popd
