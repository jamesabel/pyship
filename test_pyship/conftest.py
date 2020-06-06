import pytest
from pathlib import Path
import logging
import sys

from balsa import Balsa
from flit.build import main as flit_build

from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
from pyship import mkdirs
from test_pyship import TST_APP_PROJECT_DIR, TST_APP_DIST_DIR, write_test_app_version


class TestPyshipLoggingHandler(logging.Handler):
    def emit(self, record):
        print(record.getMessage())
        assert False


@pytest.fixture(scope="session", autouse=True)
def session_fixture():

    balsa = Balsa(pyship_application_name, pyship_author, log_directory=Path("log", "pytest"), delete_existing_log_files=True, verbose=False)

    # add handler that will throw an assert on ERROR or greater
    test_handler = TestPyshipLoggingHandler()
    test_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(test_handler)

    balsa.init_logger()

    write_test_app_version()

    # use flit to build the target app into a distributable package in the "dist" directory
    mkdirs(TST_APP_DIST_DIR)
    flit_build(Path(TST_APP_PROJECT_DIR, "pyproject.toml"))

    if pyship_application_name not in sys.path:
        sys.path.append(pyship_application_name)  # since, when testing pyship, pyship itself isn't in the venv
