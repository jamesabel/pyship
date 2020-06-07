from pathlib import Path
import json
import os

from semver import VersionInfo
from flit.build import main as flit_build

from pyship import PyShip, subprocess_run, rmdir, mkdirs
from test_pyship import TST_APP_PROJECT_DIR, TST_APP_LAUNCHER_EXE_PATH, write_test_app_version, TST_APP_FROZEN_DIR, TST_APP_NAME, TST_APP_DIST_DIR, TST_APP_VERSION


def test_update():
    """
    test that we can update the app (i.e. update pyshipy)
    """

    def do_pyship():
        mkdirs(TST_APP_DIST_DIR)
        flit_build(Path(TST_APP_PROJECT_DIR, "pyproject.toml"))  # use flit to build the target app into a distributable package in the "dist" directory
        ps = PyShip(target_app_parent_dir=TST_APP_PROJECT_DIR, find_links=["dist"])  # uses pyship under development (what's in "dist", not what's in PyPI)
        ps.ship()
        return ps

    # create the version we're going to upgrade *to* and put it in a separate dir
    updated_version = TST_APP_VERSION.bump_patch()  # bump patch to create version to be upgraded to
    write_test_app_version(updated_version)  # get default version
    do_pyship()
    upgrade_dir = Path(TST_APP_FROZEN_DIR.parent, f"{TST_APP_NAME}_{str(updated_version)}")
    rmdir(upgrade_dir)
    os.rename(TST_APP_FROZEN_DIR, upgrade_dir)

    # now create the 'original' version
    write_test_app_version(TST_APP_VERSION)
    py_ship = do_pyship()
    assert TST_APP_VERSION == py_ship.target_app_info.version

    # run the 'original' version and test that it updates itself
    return_code, std_out, std_err = subprocess_run([TST_APP_LAUNCHER_EXE_PATH], stdout_log=print)
    app_run_dict = json.loads(std_out)
    run_version_string = app_run_dict.get("version")
    run_version = VersionInfo.parse(run_version_string)
    assert run_version == updated_version
