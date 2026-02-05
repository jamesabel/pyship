from semver import VersionInfo
from pathlib import Path

import pytest
from ismain import is_main

from pyshipupdate import rmdir, ok_return_code

from pyship.launcher import launch

from test_pyship import TST_APP_NAME, TstAppDirs


def test_launcher():
    # Moto mock is enabled in conftest.py - subprocess will find empty bucket and report "no updates"
    tst_app_dirs = TstAppDirs(TST_APP_NAME, VersionInfo.parse("0.0.1"))
    clip_dir = Path(tst_app_dirs.app_dir, f"{TST_APP_NAME}_0.0.1")
    if not clip_dir.exists():
        pytest.skip(f"CLIP directory not found at {clip_dir} - run test_cloud first")
    rmdir(Path(tst_app_dirs.app_dir, "tstpyshipapp_0.0.2"))  # prior tests can write this, so make sure it doesn't exist
    assert launch(tst_app_dirs.app_dir, tst_app_dirs.app_dir) == ok_return_code


if is_main():
    test_launcher()
