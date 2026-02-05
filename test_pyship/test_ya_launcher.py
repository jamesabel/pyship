from semver import VersionInfo
from pathlib import Path

import pytest
from ismain import is_main

from pyshipupdate import rmdir

from pyship.launcher import launch
from pyship.launcher.launcher_standalone import OK_RETURN_CODE

from test_pyship import TST_APP_NAME, TstAppDirs


def test_launcher():
    # Moto mock is enabled in conftest.py - subprocess will find empty bucket and report "no updates"
    tst_app_dirs = TstAppDirs(TST_APP_NAME, VersionInfo.parse("0.0.1"))
    clip_dir = Path(tst_app_dirs.app_dir, f"{TST_APP_NAME}_0.0.1")
    if not clip_dir.exists():
        pytest.skip(f"CLIP directory not found at {clip_dir} - run test_cloud first")
    rmdir(Path(tst_app_dirs.app_dir, "tstpyshipapp_0.0.2"))  # prior tests can write this, so make sure it doesn't exist
    assert launch(app_dir=tst_app_dirs.app_dir, additional_path=tst_app_dirs.app_dir) == OK_RETURN_CODE


if is_main():
    test_launcher()
