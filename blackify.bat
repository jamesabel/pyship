REM can run into this bug
REM https://github.com/psf/black#ignoring-unmodified-files
venv\Scripts\black.exe -l 192 pyship examples\example_cli\example_cli examples\example_gui\example_gui
