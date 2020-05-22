import subprocess
import json

from test_pyship import TST_APP_LAUNCHER_EXE_PATH


def test_check_app_output():

    def check_output(p):
        app_out = json.loads(p.stdout)  # the test app prints out JSON
        assert app_out["name"] == "tstpyshipapp"
        assert app_out["version"] == "0.0.1"

    # test that the created frozen app can run correctly, including checking its output
    p = subprocess.run(str(TST_APP_LAUNCHER_EXE_PATH), cwd=TST_APP_LAUNCHER_EXE_PATH.parent, capture_output=True, text=True)
    check_output(p)
    p = subprocess.run(str(TST_APP_LAUNCHER_EXE_PATH), capture_output=True, text=True)  # check execution from a dir that's not the parent of the .exe
    check_output(p)
