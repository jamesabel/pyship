""" pyship - ship python apps """

python_interpreter_exes = {True: "pythonw.exe", False: "python.exe"}  # True is GUI, False is CLI

APP_DIR_NAME = "app"  # analogous to a "Program Files" or "Applications" directory
LIP_EXT = "lip"  # zipped lip file extension
DEFAULT_DIST_DIR_NAME = "dist"

from .__version__ import __version__, __author__, __application_name__, __title__, __description__, __url__, __author_email__, __download_url__
from .constants import dist_dir
from .date_time import local_time_string, utc_time_string
from .exe_return_codes import restart_return_code, can_not_find_file_return_code, ok_return_code, error_return_code
from .logging import PyshipLog, get_logger, log_process_output
from .pyship_print import pyship_print
from .arguments import arguments
from .subprocess_run import subprocess_run
from .app_info import AppInfo, get_app_info, get_app_info_py_project
from .get_icon import get_icon
from .nsis import run_nsis
from .file_download import file_download, extract
from .create_launcher import create_launcher
from .lip import create_base_lip, version_from_lip_zip, install_target_app, create_lip, create_lip_file
from .cloud import PyShipCloud, PyShipAWS
from .pyship import PyShip
from .main import main
