""" pyship - ship python apps """

__application_name__ = "pyship"

python_interpreter_exes = {True: "pythonw.exe", False: "python.exe"}  # True is GUI, False is CLI

from .__version__ import __version__, __author__
from .pyship_log import PyshipLog, get_logger, log_process_output
from .pyship_os import is_windows, mkdirs
from .exe_return_codes import restart_return_code, can_not_find_file_return_code, ok_return_code, error_return_code
from .pyship_print import pyship_print
from .subprocess_run import subprocess_run
from .pyship_tkinter import add_tkinter
from .target_app_info import TargetAppInfo
from .nsis import run_nsis
from .file_download import file_download, extract
from .create_launcher import create_launcher
from .module_helper import install_target_module, get_module_version
from .pyshipy import create_pyshipy
from .pyship_module import PyShip
from .pyship_main import pyship_main
