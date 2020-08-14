from semver import VersionInfo

from pyship import AppInfo, get_app_info
from pyship import __author__ as pyship_author
from test_pyship import TST_APP_NAME, TstAppDirs


def test_pyproject():
    version = VersionInfo.parse("0.0.1")
    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
    target_app_info = get_app_info(tst_app_dirs.project_dir, tst_app_dirs.dist_dir)
    assert(target_app_info.name == TST_APP_NAME)
    assert(target_app_info.author == pyship_author)
    assert(target_app_info.is_gui is not None)
    assert(target_app_info.target_app_project_dir.exists())
    assert(target_app_info.description is not None)
    assert(len(target_app_info.description) > 1)
    assert(target_app_info.version is not None)
    assert(target_app_info.version > VersionInfo.parse("0.0.0"))
