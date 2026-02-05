from pprint import pprint

from semver import VersionInfo
from balsa import get_logger

from pyship import PyShip, CLIP_EXT
from pyship.constants import is_ci
from test_pyship import TstAppDirs, TST_APP_NAME

log = get_logger(TST_APP_NAME)


def test_cloud():
    # Moto mock is enabled in conftest.py session fixture
    version = VersionInfo.parse("0.0.1")
    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
    py_ship = PyShip(tst_app_dirs.project_dir, dist_dir=tst_app_dirs.dist_dir)
    py_ship.cloud_bucket = "testawsimple"  # awsimple moto mock creates this on demand
    py_ship.cloud_profile = "default"  # with moto mock we don't need a real profile
    log.info(f"{py_ship.cloud_profile=}")
    installer_path = py_ship.ship()

    # In CI, NSIS may not be available so installer won't be created
    if installer_path is not None:
        uploaded_files = py_ship.cloud_access.s3_access.dir()
        pprint(uploaded_files)
        clip_file_name = f"{TST_APP_NAME}_{version}.{CLIP_EXT}"
        assert clip_file_name in uploaded_files
        installer_name = f"{TST_APP_NAME}_installer_win64.exe"
        assert installer_name in uploaded_files
    else:
        assert is_ci(), "Installer creation failed but not running in CI"
        log.info("Skipping upload assertions - NSIS not available in CI")
