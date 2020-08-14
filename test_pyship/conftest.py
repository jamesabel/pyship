import pytest
from pathlib import Path
import logging
import os
import time
from datetime import timedelta
from semver import VersionInfo
import subprocess

from balsa import Balsa

from pyship import __application_name__ as pyship_application_name, rmdir
from pyship import __author__ as pyship_author

from test_pyship import TST_APP_NAME, TstAppDirs


class TestPyshipLoggingHandler(logging.Handler):
    def emit(self, record):
        print(record.getMessage())
        assert False


@pytest.fixture(scope="session", autouse=True)
def session_fixture():

    balsa = Balsa(pyship_application_name, pyship_author, log_directory=Path("log", "pytest"), delete_existing_log_files=True, verbose=True)

    # add handler that will throw an assert on ERROR or greater
    test_handler = TestPyshipLoggingHandler()
    test_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(test_handler)

    balsa.init_logger()

    # create app environments

    # even though the environments rarely change, recreate the environment only if it's older than this just to make sure we still can
    env_timeout_sec = timedelta(hours=1).total_seconds()

    subprocess.run(["build.bat"], shell=True)  # update pyship wheel to the latest

    for version_string in ["0.0.1", "0.0.2"]:
        tst_app_dirs = TstAppDirs(TST_APP_NAME, VersionInfo.parse(version_string))

        rmdir(tst_app_dirs.app_dir)

        if os.path.getmtime(str(tst_app_dirs.venv_dir)) + env_timeout_sec < time.time():
            rmdir(tst_app_dirs.dist_dir)
            rmdir(tst_app_dirs.venv_dir)

            subprocess.run(["make_venv.bat"], cwd=tst_app_dirs.project_dir, shell=True)  # create the venv
            subprocess.run(["build.bat"], cwd=tst_app_dirs.project_dir, shell=True)  # make the dist (wheel)
