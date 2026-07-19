"""pyship - ship python apps"""

python_interpreter_exes = {"gui": "pythonw.exe", "cli": "python.exe", "tui": "python.exe"}

APP_DIR_NAME = "app"  # analogous to a "Program Files" or "Applications" directory
CLIP_EXT = "clip"  # zipped clip file extension
SUPPORTED_PYTHON_VERSIONS = ("3.11", "3.12", "3.13", "3.14")

from .path import NullPath
from .__version__ import __version__, __author__, __application_name__, __title__, __description__, __url__, __author_email__, __download_url__
from .windows_sdk import find_sdk_tool, WINDOWS_SDK_BIN_DIR
from .installer import INSTALLERS_DIR_NAME, installer_file_name, get_installers_dir
from .logging import PyshipLog, log_process_output
from .exceptions import PyshipException, PyshipNoProductDirectory, PyshipCouldNotGetVersion, PyshipLicenseFileDoesNotExist, PyshipInsufficientAppInfo, PyshipNoAppName
from .exceptions import PyshipNoTargetAppInfo, PyshipSigningUnavailable
from .custom_print import pyship_print
from .arguments import get_arguments
from .subprocess import subprocess_run
from .app_info import AppInfo, get_app_info, get_app_info_py_project
from .get_icon import get_icon
from .nsis import run_nsis
from .download import file_download, extract, PyshipDownloadError
from .signing import SigningConfig, DEFAULT_TIMESTAMP_URL, sign_if_configured, sign_file_token, is_token_present, is_certificate_in_store, is_rdp_session, check_signing_available
from .msix import create_msix
from .create_launcher import create_pyship_launcher
from .clip import create_base_clip, install_target_app, create_clip, create_clip_file
from .uv_util import find_or_bootstrap_uv, uv_python_install, copy_standalone_python, uv_pip_install, uv_build
from .cloud import PyShipCloud
from .pyship import PyShip
from .main import main
