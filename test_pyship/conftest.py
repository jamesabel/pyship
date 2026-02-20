import logging
import os

import pytest

from awsimple import use_moto_mock_env_var


class TestPyshipLoggingHandler(logging.Handler):
    def emit(self, record):
        print(record.getMessage())
        assert False


@pytest.fixture(scope="session", autouse=True)
def session_init():
    # Use moto mock by default unless AWSIMPLE_USE_MOTO_MOCK is explicitly set.
    # When moto is enabled, S3 buckets are created on demand and the test app's
    # update check will find an empty bucket and return "no update available"
    if os.environ.get(use_moto_mock_env_var) is None:
        os.environ[use_moto_mock_env_var] = "1"  # Enabled
