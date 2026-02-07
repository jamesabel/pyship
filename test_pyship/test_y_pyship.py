from semver import VersionInfo

from ismain import is_main
from balsa import get_logger

from pyship import PyShip
from pyship.ci import is_ci
from test_pyship import TST_APP_NAME, TstAppDirs

log = get_logger(TST_APP_NAME)


def test_pyship():
    version = VersionInfo.parse("0.0.1")
    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
    py_ship = PyShip(tst_app_dirs.project_dir, dist_dir=tst_app_dirs.dist_dir)
    installer_path = py_ship.ship()

    # In CI, NSIS may not be available so installer won't be created
    if installer_path is None:
        assert is_ci(), "Installer creation failed but not running in CI"
        log.info("Installer not created - NSIS not available in CI")
    else:
        assert installer_path.exists()


if is_main():
    # avoid test setup that cleans up frozen dir
    test_pyship()
