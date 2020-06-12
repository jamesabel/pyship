from pathlib import Path
from semver import VersionInfo

from pyship import mkdirs, subprocess_run, get_logger, __application_name__

TST_APP_NAME = "tstpyshipapp"


log = get_logger(__application_name__)


class TstAppDirs:
    def __init__(self, target_app_name: str, version: VersionInfo):

        self.target_app_name = target_app_name
        self.target_app_version = version

        self.project_dir = Path("test_pyship", f"{self.target_app_name}_{str(self.target_app_version)}")
        self.app_parent = Path(self.project_dir, "app")
        self.app_dir = Path(self.app_parent, self.target_app_name)
        self.cache = Path(self.project_dir, "cache")
        self.dist_dir = Path(self.project_dir, "dist")
        self.launcher_exe_path = Path(self.app_dir, self.target_app_name, f"{TST_APP_NAME}.exe")


def tst_app_flit_build(tst_app_dirs: TstAppDirs):
    """
    build the test app as a package
    :param tst_app_dirs: instance of a test app dirs
    """
    mkdirs(tst_app_dirs.dist_dir, remove_first=True)
    flit_exe_path = Path("venv", "Scripts", "flit.exe")
    pyproject_path = Path(tst_app_dirs.project_dir, "pyproject.toml")
    if not flit_exe_path.exists():
        log.error(f"{flit_exe_path} does not exist")
    elif not pyproject_path.exists():
        log.error(f"{pyproject_path} does not exist")
    else:
        # use flit to build the target app into a distributable package in the "dist" directory
        subprocess_run([str(flit_exe_path), "-f", str(pyproject_path), "build"], stdout_log=print)
