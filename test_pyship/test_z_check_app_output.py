import subprocess
import json

import pytest
from semver import VersionInfo

from typeguard import typechecked

from pyshipupdate import ok_return_code

from test_pyship import TstAppDirs
from test_pyship import TST_APP_NAME


def test_check_app_output():
    # Moto mock is enabled in conftest.py - subprocess will find empty bucket and report "no updates"
    # Try 0.0.1 first (built by test_cloud), fall back to 0.0.2
    version = VersionInfo.parse("0.0.1")
    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
    if not tst_app_dirs.launcher_exe_path.exists():
        version = VersionInfo.parse("0.0.2")
        tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
        if not tst_app_dirs.launcher_exe_path.exists():
            pytest.skip(f"Launcher exe not found at {tst_app_dirs.launcher_exe_path} - run test_cloud first")

    @typechecked
    def check_output(check_process: subprocess.CompletedProcess):
        lines = [ln.strip() for ln in check_process.stdout.splitlines() if len(ln.strip()) > 0]
        assert len(lines) > 0
        app_out = json.loads(lines[-1])  # the test app prints out JSON
        print(app_out)
        assert app_out["name"] == TST_APP_NAME
        app_version = app_out["version"]
        assert VersionInfo.parse(app_version) == version or VersionInfo.parse(app_version) == version.bump_patch()  # allow either original or upgraded version
        assert app_out["exit_code"] == ok_return_code

    # test that the created frozen app can run correctly, including checking its output
    cmd = [str(tst_app_dirs.launcher_exe_path), "-v"]
    p = subprocess.run(cmd, cwd=tst_app_dirs.launcher_exe_path.parent, capture_output=True, text=True)
    check_output(p)
    p = subprocess.run(cmd, capture_output=True, text=True)  # check execution from a dir that's not the parent of the .exe
    check_output(p)
