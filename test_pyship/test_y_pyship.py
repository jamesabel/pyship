from semver import VersionInfo

from ismain import is_main

from pyship import PyShip
from test_pyship import TST_APP_NAME, TstAppDirs


def test_pyship():
    version = VersionInfo.parse("0.0.1")
    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
    py_ship = PyShip(tst_app_dirs.project_dir, dist_dir=tst_app_dirs.dist_dir)
    py_ship.ship()


if is_main():
    # avoid test setup that cleans up frozen dir
    test_pyship()
