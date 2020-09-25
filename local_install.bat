REM install pyship into the local venv - this is only needed for pyship development itself
call build.bat
venv\Scripts\pip.exe uninstall -y pyship
venv\Scripts\pip.exe install pyship --no-index -f dist
