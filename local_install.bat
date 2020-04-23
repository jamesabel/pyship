REM install pyship into the local venv - this is only needed for pyship development itself
call venv\scripts\activate.bat
flit install
deactivate
