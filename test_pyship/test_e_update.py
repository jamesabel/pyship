import json
from pathlib import Path

from semver import VersionInfo

from pyship import PyShip, subprocess_run, get_logger, __application_name__, pyship_print, TargetAppInfo
from test_pyship import TST_APP_NAME, tst_app_flit_build, TstAppDirs

log = get_logger(__application_name__)


def test_update():
    """
    test that we can update the app (i.e. update pyshipy)
    """

    pyship_dist_dir = Path("dist").resolve().absolute()

    def do_pyship(tst_app_dirs: TstAppDirs):
        pyship_print(f"{tst_app_dirs.target_app_version=}")
        tst_app_flit_build(tst_app_dirs)
        ps = PyShip(tst_app_dirs.project_dir, find_links=[pyship_dist_dir])  # uses pyship under development (what's in "dist", not what's in PyPI)
        inst = ps.ship_installer()
        return ps, inst

    # create the version we're going to upgrade *to* and put it in a separate dir
    updated_version = VersionInfo(0, 0, 2)
    updated_app_dirs = TstAppDirs(TST_APP_NAME, updated_version)
    updated_pyship, installer_exe_path = do_pyship(updated_app_dirs)  # bump patch to create version to be upgraded to
    assert installer_exe_path is not None
    assert installer_exe_path.exists()

    # now create the 'original' version
    original_version = VersionInfo(0, 0, 1)
    original_app_dirs = TstAppDirs(TST_APP_NAME, original_version)
    py_ship, installer_exe_path = do_pyship(original_app_dirs)
    assert installer_exe_path is not None
    assert installer_exe_path.exists()

    # Check that the app is the same for both copies. We need the same file in 2 different places for the test infrastructure, but they have
    # to have the same functional contents.
    app_contents = [open(Path(ps.project_dir, TST_APP_NAME, "app.py")).read() for ps in [py_ship, updated_pyship]]
    assert app_contents[0] == app_contents[1]

    # run the 'original' app version and test that it updates itself
    cmd = [original_app_dirs.launcher_exe_path]

    # uncomment for detailed debugging
    cmd.append("--launcher_verbose")

    # run the app from it's own directory
    return_code, std_out, std_err = subprocess_run(cmd, cwd=original_app_dirs.launcher_exe_path.parent, stdout_log=pyship_print)

    # we'll get multiple version JSON strings (one per line)
    lines = [ln.strip() for ln in std_out.splitlines() if len(ln.strip()) > 0]
    for i, version_string in enumerate(["0.0.1", "0.0.2"]):
        app_run_dict = json.loads(lines[i])
        run_version_string = app_run_dict.get("version")
        run_version = VersionInfo.parse(run_version_string)
        assert run_version == VersionInfo.parse(version_string)
