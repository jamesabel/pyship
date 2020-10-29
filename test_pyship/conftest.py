import pytest
from pathlib import Path
import logging
import os

from balsa import Balsa
from awsimple import use_moto_mock_env_var

from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author


class TestPyshipLoggingHandler(logging.Handler):
    def emit(self, record):
        print(record.getMessage())
        assert False


@pytest.fixture(scope="session", autouse=True)
def session_fixture():

    os.environ[use_moto_mock_env_var] = "1"

    balsa = Balsa(pyship_application_name, pyship_author, log_directory=Path("log", "pytest"), delete_existing_log_files=True, verbose=False)

    # add handler that will throw an assert on ERROR or greater
    test_handler = TestPyshipLoggingHandler()
    test_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(test_handler)

    balsa.init_logger()
