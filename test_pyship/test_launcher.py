from semver import VersionInfo
from pathlib import Path

from ismain import is_main

from pyship import ok_return_code, rmdir

from pyship.launcher import launch

from test_pyship import TST_APP_NAME, TstAppDirs


def test_launcher():
    tst_app_dirs = TstAppDirs(TST_APP_NAME, VersionInfo.parse("0.0.1"))
    rmdir(Path(tst_app_dirs.app_dir, "tstpyshipapp_0.0.2"))  # prior tests can write this, so make sure it doesn't exist
    assert launch(tst_app_dirs.app_dir, tst_app_dirs.app_dir) == ok_return_code


if is_main():
    test_launcher()
