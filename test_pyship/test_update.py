from pathlib import Path
import json
import os

from semver import VersionInfo

from pyship import PyShip, subprocess_run, rmdir, get_logger, __application_name__, pyship_print
from test_pyship import TST_APP_PROJECT_DIR, TST_APP_LAUNCHER_EXE_PATH, write_test_app_version, TST_APP_FROZEN_PARENT, TST_APP_VERSION, test_app_flit_build, TST_APP_DIST_DIR

log = get_logger(__application_name__)


def test_update():
    """
    test that we can update the app (i.e. update pyshipy)
    """

    def do_pyship(version: VersionInfo):
        pyship_print(f"{version=}")
        write_test_app_version(version)
        test_app_flit_build()
        ps = PyShip(target_app_parent_dir=TST_APP_PROJECT_DIR, find_links=["dist"])  # uses pyship under development (what's in "dist", not what's in PyPI)
        ps.ship()
        return ps

    # create the version we're going to upgrade *to* and put it in a separate dir
    updated_version = TST_APP_VERSION.bump_patch()
    do_pyship(updated_version)  # bump patch to create version to be upgraded to
    for d in TST_APP_FROZEN_PARENT, TST_APP_DIST_DIR:
        upgrade_dir = Path(d.parent, f"{d.name}_{updated_version}")
        rmdir(upgrade_dir)
        os.rename(d, upgrade_dir)

    # now create the 'original' version
    py_ship = do_pyship(TST_APP_VERSION)
    assert TST_APP_VERSION == py_ship.target_app_info.version  # make sure we just made the intended version

    # run the 'original' version and test that it updates itself
    return_code, std_out, std_err = subprocess_run([TST_APP_LAUNCHER_EXE_PATH], stdout_log=print)
    app_run_dict = json.loads(std_out)
    run_version_string = app_run_dict.get("version")
    run_version = VersionInfo.parse(run_version_string)
    assert run_version == updated_version
