import pytest
from pathlib import Path
import logging
import sys

from balsa import Balsa

from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
from pyship import mkdirs
from test_pyship import TST_APP_FROZEN_DIR


class TestPyshipLoggingHandler(logging.Handler):
    def emit(self, record):
        print(record.getMessage())
        assert False


@pytest.fixture(scope="session", autouse=True)
def session_fixture(request):

    def remove_test_dir():
        mkdirs(TST_APP_FROZEN_DIR, remove_first=True)  # there are test_* files in the python dist (i.e. will be in pyshipy), so we have to delete them on exit
    request.addfinalizer(remove_test_dir)

    balsa = Balsa(pyship_application_name, pyship_author, log_directory=Path("log", "pytest"), delete_existing_log_files=True, verbose=False)

    # add handler that will throw an assert on ERROR or greater
    test_handler = TestPyshipLoggingHandler()
    test_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(test_handler)

    balsa.init_logger()

    if pyship_application_name not in sys.path:
        sys.path.append(pyship_application_name)  # since, when testing pyship, pyship itself isn't in the venv
