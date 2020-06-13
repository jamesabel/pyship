import pytest
from pathlib import Path
import logging
import sys

from balsa import Balsa

from pyship import mkdirs, subprocess_run, pyship_print
from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
from pyship import __version__ as pyship_version

from test_pyship import VERBOSE


class TestPyshipLoggingHandler(logging.Handler):
    def emit(self, record):
        print(record.getMessage())
        assert False


@pytest.fixture(scope="session", autouse=True)
def session_fixture():

    balsa = Balsa(pyship_application_name, pyship_author, log_directory=Path("log", "pytest"), delete_existing_log_files=True, verbose=VERBOSE)

    # add handler that will throw an assert on ERROR or greater
    test_handler = TestPyshipLoggingHandler()
    test_handler.setLevel(logging.ERROR)
    logging.getLogger().addHandler(test_handler)

    balsa.init_logger()

    # use flit to build pyship into a distributable package in the "dist" directory
    mkdirs(Path("dist"), remove_first=True)
    subprocess_run([str(Path("venv", "Scripts", "flit.exe")), "build"], mute_output=True, stderr_log=logging.info)  # flit writes output to stderr, not sure why
    pyship_print(f"{pyship_application_name=} {pyship_version=} {pyship_author=}")

    if pyship_application_name not in sys.path:
        sys.path.append(pyship_application_name)  # since, when testing pyship, pyship itself isn't in the venv
