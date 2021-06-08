""" pyship - ship python apps """

python_interpreter_exes = {True: "pythonw.exe", False: "python.exe"}  # True is GUI, False is CLI

APP_DIR_NAME = "app"  # analogous to a "Program Files" or "Applications" directory
CLIP_EXT = "clip"  # zipped clip file extension
DEFAULT_DIST_DIR_NAME = "dist"

from .pyship_path import NullPath
from ._version_ import __version__, __author__, __application_name__, __title__, __description__, __url__, __author_email__, __download_url__
from .logging import PyshipLog, log_process_output
from .pyship_exceptions import PyshipException, PyshipNoProductDirectory, PyshipCouldNotGetVersion, PyshipLicenseFileDoesNotExist, PyshipInsufficientAppInfo
from .constants import dist_dir
from .pyship_custom_print import pyship_print
from .arguments import get_arguments
from .pyship_subprocess import subprocess_run
from .app_info import AppInfo, get_app_info, get_app_info_py_project
from .pyship_get_icon import get_icon
from .nsis import run_nsis
from .download import file_download, extract
from .create_launcher import create_pyship_launcher
from .clip import create_base_clip, install_target_app, create_clip, create_clip_file
from .cloud import PyShipCloud
from .pyship import PyShip
from .main import main
