""" pyship - ship python apps """

__application_name__ = "pyship"

python_interpreter_exes = {True: "pythonw.exe", False: "python.exe"}  # True is GUI, False is CLI

APP_DIR_NAME = "app"  # analogous to a "Program Files" or "Applications" directory
LIP_EXT = "lip"  # zipped lip file extension
DEFAULT_DIST_DIR_NAME = "dist"

from .__version__ import __version__, __author__
from .date_time import local_time_string, utc_time_string
from .exe_return_codes import restart_return_code, can_not_find_file_return_code, ok_return_code, error_return_code
from .logging import PyshipLog, get_logger, log_process_output
from .pyship_print import pyship_print
from .arguments import arguments
from .os_util import is_windows, mkdirs, rmdir, copy_tree, get_target_os
from .subprocess_run import subprocess_run
from .app_info import AppInfo, get_app_info
from .nsis import run_nsis
from .file_download import file_download, extract
from .create_launcher import create_launcher
from .lip import create_base_lip, version_from_lip_zip, install_target_app, create_lip, create_lib_file
from .pyship import PyShip
from .main import main
