import pytest
from pathlib import Path
import logging
import os
import subprocess

from balsa import Balsa
from appdirs import user_data_dir
from awsimple import use_moto_mock_env_var

from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
from pyship import pyship_print
from pyshipupdate import rmdir

from test_pyship import TST_APP_NAME, __application_name__


class TestPyshipLoggingHandler(logging.Handler):
    def emit(self, record):
        print(record.getMessage())
        assert False


@pytest.fixture(scope="module", autouse=True)
def module_init():
    clip_dir = Path(user_data_dir(TST_APP_NAME, pyship_author), f"{TST_APP_NAME}_0.0.2")
    rmdir(clip_dir)  # clip dir in appdata local can be left over from prior runs


@pytest.fixture(scope="session", autouse=True)
def session_init():
    # Use moto mock by default unless AWSIMPLE_USE_MOTO_MOCK is explicitly set to "0"
    # When moto is enabled, S3 buckets are created on demand and the test app's
    # update check will find an empty bucket and return "no update available"
    if os.environ.get(use_moto_mock_env_var, "1") != "0":
        os.environ[use_moto_mock_env_var] = "1"

    # delete any existing venvs, builds, etc. of the test apps
    subdirs = ["venv", "dist"]
    for subdir in subdirs:
        for p in Path(__application_name__).glob(f"{TST_APP_NAME}*/{subdir}"):
            pyship_print(f'removing "{p}"')
            rmdir(p)

    # build pyship package itself
    build_bat_file_path = Path("build.bat")
    pyship_print(f'running "{build_bat_file_path}" ("{build_bat_file_path.absolute()}")')
    subprocess.run(str(build_bat_file_path), capture_output=True, shell=True)

    balsa = Balsa(pyship_application_name, pyship_author, log_directory=Path("log", "pytest"), delete_existing_log_files=True, verbose=False)

    # add handler that will throw an assert on ERROR or greater
    test_handler = TestPyshipLoggingHandler()
    test_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(test_handler)

    balsa.init_logger()
