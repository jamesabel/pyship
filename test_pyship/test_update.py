import json

from semver import VersionInfo

from pyship import PyShip, subprocess_run, get_logger, __application_name__, pyship_print
from test_pyship import TST_APP_NAME, tst_app_flit_build, TstAppDirs

log = get_logger(__application_name__)


def test_update():
    """
    test that we can update the app (i.e. update pyshipy)
    """

    def do_pyship(tst_app_dirs: TstAppDirs):
        pyship_print(f"{tst_app_dirs.target_app_version=}")
        tst_app_flit_build(tst_app_dirs)
        ps = PyShip(target_app_parent_dir=tst_app_dirs.project_dir, find_links=["dist"])  # uses pyship under development (what's in "dist", not what's in PyPI)
        ps.ship()
        return ps

    # create the version we're going to upgrade *to* and put it in a separate dir
    updated_version = VersionInfo(0, 0, 2)
    updated_app_dirs = TstAppDirs(TST_APP_NAME, updated_version)
    do_pyship(updated_app_dirs)  # bump patch to create version to be upgraded to

    # now create the 'original' version
    original_version = VersionInfo(0, 0, 1)
    original_app_dirs = TstAppDirs(TST_APP_NAME, original_version)
    py_ship = do_pyship(original_app_dirs)
    assert original_version == py_ship.target_app_info.version  # make sure we just made the intended version

    # run the 'original' version and test that it updates itself
    return_code, std_out, std_err = subprocess_run([original_app_dirs.launcher_exe_path], stdout_log=print)
    app_run_dict = json.loads(std_out)
    run_version_string = app_run_dict.get("version")
    run_version = VersionInfo.parse(run_version_string)
    assert run_version == updated_version
