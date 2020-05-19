""" pyship - ship python apps """

__application_name__ = "pyship"

python_interpreter_exes = {True: "pythonw.exe", False: "python.exe"}  # True is GUI, False is CLI

from .__version__ import __version__, __author__
from .logging import PyshipLog, get_logger, log_process_output
from .os_util import is_windows, mkdirs
from .exe_return_codes import restart_return_code, can_not_find_file_return_code, ok_return_code, error_return_code
from .pyship_print import pyship_print
from .subprocess_run import subprocess_run
from .target_app_info import TargetAppInfo
from .nsis import run_nsis
from .file_download import file_download, extract
from .create_launcher import create_launcher
from .module_util import install_target_module, get_module_version
from .pyshipy import create_pyshipy, add_tkinter
from .pyship import PyShip
from .main import main
