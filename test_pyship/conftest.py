import pytest
from pathlib import Path

from balsa import Balsa

from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    balsa = Balsa(pyship_application_name, pyship_author, log_directory=Path("log", "pytest"), delete_existing_log_files=True, verbose=True)
    balsa.init_logger()
