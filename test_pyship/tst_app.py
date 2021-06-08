from pathlib import Path
from semver import VersionInfo

from balsa import get_logger

from pyship import __application_name__, APP_DIR_NAME

TST_APP_NAME = "tstpyshipapp"


log = get_logger(__application_name__)


class TstAppDirs:
    def __init__(self, target_app_name: str, version: VersionInfo):

        self.target_app_name = target_app_name
        self.target_app_version = version

        self.project_subdir = f"{self.target_app_name}_{str(self.target_app_version)}"
        self.project_dir = Path("test_pyship", self.project_subdir).absolute()
        self.app_dir = Path(self.project_dir, APP_DIR_NAME, self.target_app_name)
        self.cache = Path(self.project_dir, "cache")
        self.venv_dir = Path(self.project_dir, "venv")
        self.dist_dir = Path(self.project_dir, "dist")
        self.launcher_exe_path = Path(self.app_dir, self.target_app_name, f"{TST_APP_NAME}.exe")
