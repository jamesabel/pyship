from ismain import is_main
from semver import VersionInfo
from pathlib import Path

from pyship import create_clip, AppInfo, PyshipLog, get_logger, __author__

from test_pyship import TstAppDirs, TST_APP_NAME, __application_name__, find_links

log = get_logger(__application_name__)


def test_create_clip():

    version = VersionInfo.parse("0.0.1")
    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
    app_info = AppInfo(TST_APP_NAME, __author__, version)
    app_info.setup_paths(tst_app_dirs.project_dir)
    lip_dir = create_clip(app_info, tst_app_dirs.app_dir, True, tst_app_dirs.dist_dir, tst_app_dirs.cache, find_links)
    log.info(f"{lip_dir=}")
    assert Path(lip_dir, "python.exe").exists()  # make sure base python created
    assert Path(lip_dir, "Lib", "site-packages", "pyship").exists()  # make sure pyship has been installed (we're using pyship itself in this test)


if is_main():
    pyship_log = PyshipLog(__application_name__, __author__, log_directory="log", delete_existing_log_files=True, verbose=True)
    pyship_log.init_logger()
    test_create_clip()
