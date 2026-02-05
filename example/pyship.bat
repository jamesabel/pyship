@echo on
call venv\Scripts\activate.bat
python -m pyship --noupload
deactivate
