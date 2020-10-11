import subprocess
import json
from semver import VersionInfo

from typeguard import typechecked

from pyship import ok_return_code

from test_pyship import TstAppDirs
from test_pyship import TST_APP_NAME


def test_check_app_output():

    version = VersionInfo.parse("0.0.2")  # must be run after other tests that create the test app with this version

    @typechecked(always=True)
    def check_output(check_process: subprocess.CompletedProcess):
        lines = [ln.strip() for ln in check_process.stdout.splitlines() if len(ln.strip()) > 0]
        assert len(lines) > 0
        app_out = json.loads(lines[-1])  # the test app prints out JSON
        print(app_out)
        assert app_out["name"] == TST_APP_NAME
        app_version = app_out["version"]
        assert VersionInfo.parse(app_version) == version or VersionInfo.parse(app_version) == version.bump_patch()  # allow either original or upgraded version
        assert app_out["exit_code"] == ok_return_code

    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)

    # test that the created frozen app can run correctly, including checking its output
    cmd = [str(tst_app_dirs.launcher_exe_path), "-v"]
    p = subprocess.run(cmd, cwd=tst_app_dirs.launcher_exe_path.parent, capture_output=True, text=True)
    check_output(p)
    p = subprocess.run(cmd, capture_output=True, text=True)  # check execution from a dir that's not the parent of the .exe
    check_output(p)
