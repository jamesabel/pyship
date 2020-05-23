import subprocess
import json

from typeguard import typechecked

from test_pyship import TST_APP_LAUNCHER_EXE_PATH
from test_pyship.tstpyshipapp.tstpyshipapp import __version__ as tstpyshipapp_version
from test_pyship.tstpyshipapp.tstpyshipapp import __application_name__ as tstpyshipapp_name


def test_check_app_output():

    @typechecked(always=True)
    def check_output(check_process: subprocess.CompletedProcess):
        app_out = json.loads(check_process.stdout)  # the test app prints out JSON
        assert app_out["name"] == tstpyshipapp_name
        assert app_out["version"] == tstpyshipapp_version

    # test that the created frozen app can run correctly, including checking its output
    p = subprocess.run(str(TST_APP_LAUNCHER_EXE_PATH), cwd=TST_APP_LAUNCHER_EXE_PATH.parent, capture_output=True, text=True)
    check_output(p)
    p = subprocess.run(str(TST_APP_LAUNCHER_EXE_PATH), capture_output=True, text=True)  # check execution from a dir that's not the parent of the .exe
    check_output(p)
