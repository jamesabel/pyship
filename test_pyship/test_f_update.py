import json
from json.decoder import JSONDecodeError
from pathlib import Path

from semver import VersionInfo
from awsimple import S3Access

from pyship import PyShip, subprocess_run, get_logger, __application_name__, pyship_print
from test_pyship import TST_APP_NAME, TstAppDirs, find_links

log = get_logger(__application_name__)


def test_update():
    """
    test that we can update the app
    """

    def do_pyship(tst_app_dirs: TstAppDirs):
        pyship_print(f"{tst_app_dirs.target_app_version=}")
        ps = PyShip(tst_app_dirs.project_dir, dist_dir=tst_app_dirs.dist_dir,
                    find_links=find_links  # the local pyship under development
                    )
        inst = ps.ship_installer()
        return ps, inst

    S3Access(TST_APP_NAME).create_bucket()
    original_version = VersionInfo(0, 0, 1)
    updated_version = VersionInfo(0, 0, 2)
    original_app_dirs = TstAppDirs(TST_APP_NAME, original_version)
    pyships = []
    for version in [original_version, updated_version]:
        app_dirs = TstAppDirs(TST_APP_NAME, version)
        ps, installer_exe_path = do_pyship(app_dirs)  # bump patch to create version to be upgraded to
        pyships.append(ps)
        assert installer_exe_path is not None
        assert installer_exe_path.exists()

    # Check that the app is the same for both copies. We need the same file in 2 different places for the test infrastructure, but they have
    # to have the same functional contents.
    app_contents = [open(Path(ps.project_dir, TST_APP_NAME, "app.py")).read() for ps in pyships]
    assert app_contents[0] == app_contents[1]

    # run the 'original' app version and test that it updates itself
    cmd = [original_app_dirs.launcher_exe_path]

    # uncomment for detailed debugging
    # cmd.append("--launcher_verbose")

    # run the app from its own directory
    return_code, std_out, std_err = subprocess_run(cmd, cwd=original_app_dirs.launcher_exe_path.parent, stdout_log=pyship_print)

    # we'll get multiple version JSON strings (one per line)
    lines = [ln.strip() for ln in std_out.splitlines() if len(ln.strip()) > 0]
    log.info(f"{lines=}")
    assert len(lines) == 2
    for i, version_string in enumerate(["0.0.1", "0.0.2"]):
        one_line = lines[i]
        print(one_line)
        log.info(one_line)
        try:
            app_run_dict = json.loads(one_line)
            run_version_string = app_run_dict.get("version")
            run_version = VersionInfo.parse(run_version_string)
        except JSONDecodeError as e:
            log.warning(f"{one_line},{e}")  # just output (a log.error() does an assert, and we're doing the assert below)
            run_version = None
        assert run_version == VersionInfo.parse(version_string)
