import os
from pprint import pprint

from semver import VersionInfo
from balsa import get_logger

from pyship import PyShip, CLIP_EXT
from test_pyship import TstAppDirs, TST_APP_NAME

log = get_logger(TST_APP_NAME)


def test_cloud():

    version = VersionInfo.parse("0.0.1")
    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
    py_ship = PyShip(tst_app_dirs.project_dir, dist_dir=tst_app_dirs.dist_dir)
    py_ship.cloud_bucket = "testawsimple"  # awsimple moto mock makes this
    py_ship.cloud_profile = os.environ.get("CLOUD_PROFILE", "default")  # since we're using moto to mock we don't need a real profile
    log.info(f"{py_ship.cloud_profile=}")
    py_ship.ship_installer()

    uploaded_files = py_ship.cloud_access.s3_access.dir()
    pprint(uploaded_files)
    clip_file_name = f"{TST_APP_NAME}_{version}.{CLIP_EXT}"
    assert clip_file_name in uploaded_files
    installer_name = f"{TST_APP_NAME}_installer_win64.exe"
    assert installer_name in uploaded_files
