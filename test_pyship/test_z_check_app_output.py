import subprocess
import json
from semver import VersionInfo

from typeguard import typechecked

from test_pyship import TstAppDirs
from test_pyship import TST_APP_NAME


def test_check_app_output():

    version = VersionInfo.parse("0.0.1")

    @typechecked(always=True)
    def check_output(check_process: subprocess.CompletedProcess):
        app_out = json.loads(check_process.stdout)  # the test app prints out JSON
        assert app_out["name"] == TST_APP_NAME
        assert app_out["version"] == version

    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
    # test that the created frozen app can run correctly, including checking its output
    cmd = [str(tst_app_dirs.launcher_exe_path), "-v"]
    p = subprocess.run(cmd, cwd=tst_app_dirs.launcher_exe_path.parent, capture_output=True, text=True)
    check_output(p)
    p = subprocess.run(cmd, capture_output=True, text=True)  # check execution from a dir that's not the parent of the .exe
    check_output(p)
