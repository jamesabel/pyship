from pathlib import Path
import subprocess
import json

from semver import VersionInfo

from pyship import PyShip, subprocess_run
from test_pyship import TST_APP_PROJECT_DIR, TST_APP_LAUNCHER_EXE_PATH


class TstPyShip(PyShip):
    def set_frozen_app_dir(self):
        """
        set frozen app dir (override this to use a different frozen app dir)
        """
        self.frozen_app_dir = Path(self.target_app_parent_dir, self.frozen_app_dir_name, f"{self.target_app_info.name}_2").absolute()


def test_update():
    """
    test that we can update the app (i.e. update pyshipy)
    """

    # todo:
    # create an app (with some version, say 0.0.1) that does an automatic update and when it exits it prints the version number (to stdout)
    # freeze that app into some temp dir (emulates the install)
    # create an update of that app (a pyshipy dir) with a higher version (say 0.0.2) and "release" that version (which zips the pyshipy dir and copies it up to S3).
    # run the original frozen app via the launcher.  if it works, it will auto-update. capture it's output
    # check that the original frozen app prints out the 2 version strings when it exits

    # initial version
    initial_py_ship = PyShip(target_app_parent_dir=TST_APP_PROJECT_DIR)

    # updated version
    updated_py_ship = TstPyShip(target_app_parent_dir=TST_APP_PROJECT_DIR)
    updated_py_ship.target_app_info.version.bump_patch()  # inject a version higher than the original

    # run first with initial version and check the version, then run updated version and check the version
    for py_ship in [initial_py_ship, updated_py_ship]:

        # todo: DEBUG
        py_ship.ship()

        return_code, std_out, std_err = subprocess_run([TST_APP_LAUNCHER_EXE_PATH])  # always the same app exe, first time through does an update
        for out in [std_out, std_err]:
            if out is not None and len(out) > 0:
                print(out)

        app_run_dict = json.loads(std_out)
        run_version_string = app_run_dict.get("version")
        run_version = VersionInfo.parse(run_version_string)

        assert run_version == py_ship.target_app_info.version
