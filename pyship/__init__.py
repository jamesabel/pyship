""" pyship - ship python apps """

__application_name__ = "pyship"

python_interpreter_exes = {True: "pythonw.exe", False: "python.exe"}  # True is GUI, False is CLI

from .__version__ import __version__, __author__
from .exe_return_codes import restart_return_code, can_not_find_file_return_code, ok_return_code, error_return_code
from .pyship_log import PyshipLog, get_logger, log_process_output
from .pyship_print import pyship_print
from .subprocess_run import subprocess_run
from .target_app_info import TargetAppInfo
from .util import get_pyship_sub_dir, get_file, get_folder_size, extract
from .pyship_module import PyShip, create_launcher
from .pyship_main import pyship_main
