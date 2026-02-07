"""pyship - ship python apps"""

python_interpreter_exes = {True: "pythonw.exe", False: "python.exe"}  # True is GUI, False is CLI

APP_DIR_NAME = "app"  # analogous to a "Program Files" or "Applications" directory
CLIP_EXT = "clip"  # zipped clip file extension

from .path import NullPath
from .__version__ import __version__, __author__, __application_name__, __title__, __description__, __url__, __author_email__, __download_url__
from .logging import PyshipLog, log_process_output
from .exceptions import PyshipException, PyshipNoProductDirectory, PyshipCouldNotGetVersion, PyshipLicenseFileDoesNotExist, PyshipInsufficientAppInfo, PyshipNoAppName
from .exceptions import PyshipNoTargetAppInfo
from .custom_print import pyship_print
from .arguments import get_arguments
from .subprocess import subprocess_run
from .app_info import AppInfo, get_app_info, get_app_info_py_project
from .get_icon import get_icon
from .nsis import run_nsis
from .download import file_download, extract
from .create_launcher import create_pyship_launcher
from .clip import create_base_clip, install_target_app, create_clip, create_clip_file
from .uv_util import find_or_bootstrap_uv, uv_python_install, uv_venv_create, uv_pip_install, uv_build
from .cloud import PyShipCloud
from .pyship import PyShip
from .main import main
