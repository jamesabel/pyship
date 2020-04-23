REM pyship the app
call venv\Scripts\activate.bat
REM remove the --pyship_dist_dir when pyship is on PyPI
python -m pyship --pyship_dist_dir "..\..\dist"
deactivate
