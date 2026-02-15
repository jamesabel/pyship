import pytest
from ismain import is_main
from semver import VersionInfo
from pathlib import Path

from balsa import get_logger

from pyship import create_clip, AppInfo, PyshipLog, __author__, SUPPORTED_PYTHON_VERSIONS

from test_pyship import TstAppDirs, TST_APP_NAME, __application_name__

log = get_logger(__application_name__)


@pytest.mark.parametrize("python_version", SUPPORTED_PYTHON_VERSIONS)
def test_create_clip(python_version):
    version = VersionInfo.parse("0.0.1")
    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
    app_info = AppInfo(TST_APP_NAME, __author__, version)
    app_info.setup_paths(tst_app_dirs.project_dir)
    clip_dir = create_clip(app_info, tst_app_dirs.app_dir, tst_app_dirs.dist_dir, tst_app_dirs.cache, python_version=python_version)
    log.info(f"{clip_dir=}")
    assert Path(clip_dir, "python.exe").exists()  # make sure standalone python copied to clip root
    assert Path(clip_dir, "Lib", "site-packages", "pyship").exists()  # make sure pyship has been installed (we're using pyship itself in this test)


if is_main():
    pyship_log = PyshipLog(__application_name__, __author__, log_directory="log", delete_existing_log_files=True, verbose=True)
    pyship_log.init_logger()
    test_create_clip("3.13")
