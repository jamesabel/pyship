import json
import os
from json.decoder import JSONDecodeError
from pathlib import Path
from pprint import pprint

import pytest
from semver import VersionInfo
from balsa import get_logger
from awsimple import use_moto_mock_env_var

from pyshipupdate import UpdaterAwsS3

from pyship import PyShip, subprocess_run, __application_name__, pyship_print, PyShipCloud, __author__
from test_pyship import TST_APP_NAME, TstAppDirs, find_links

log = get_logger(__application_name__)


@pytest.mark.skipif(
    os.environ.get(use_moto_mock_env_var, "1") == "1", reason="Update test requires real AWS (subprocess can't share moto mock state). Set AWSIMPLE_USE_MOTO_MOCK=0 with valid credentials."
)
def test_update():
    """
    test that we can update the app
    """

    updater = UpdaterAwsS3(TST_APP_NAME, __author__)
    pyship_cloud = PyShipCloud(TST_APP_NAME, updater)
    assert not pyship_cloud.s3_access.is_mocked()  # this test only works with the real AWS since the launched processes don't have access to the env var to make AWSimple mock
    pyship_cloud.s3_access.create_bucket()  # is this necessary?

    def do_pyship(tst_app_dirs: TstAppDirs):
        pyship_print(f"{tst_app_dirs.target_app_version=}")
        _ps = PyShip(tst_app_dirs.project_dir, dist_dir=tst_app_dirs.dist_dir, cloud_profile="pyshiptest", find_links=find_links)  # the local pyship under development
        _ps.cloud_access = pyship_cloud
        inst = _ps.ship()
        return _ps, inst

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
    pprint(lines)
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
