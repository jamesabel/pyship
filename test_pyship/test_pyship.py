from semver import VersionInfo
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pyship import SUPPORTED_PYTHON_VERSIONS, PyShip
from pyship import __application_name__ as pyship_application_name

from .make_test_app import make_test_app

@pytest.mark.parametrize("python_version", SUPPORTED_PYTHON_VERSIONS)
def test_create_clip(python_version):

    with TemporaryDirectory(prefix=pyship_application_name) as temp_dir:
        print(f'temp_dir="{temp_dir}"')
        version = VersionInfo.parse("0.0.1")
        application_name = "tstpyshipapp"
        project_dir = Path(temp_dir, "project")
        make_test_app(project_dir, application_name, version, python_version, False)  # dynamically create the test app
        pyship = PyShip(project_dir, upload=False)
        pyship.ship()

