from semver import VersionInfo
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from pyship import create_clip, AppInfo, __author__, SUPPORTED_PYTHON_VERSIONS
from pyship import __application_name__ as pyship_application_name

from .make_test_app import make_test_app

# @pytest.mark.parametrize("python_version", SUPPORTED_PYTHON_VERSIONS)
# def test_create_clip(python_version):
def test_create_clip():

    test_name = "test_create_clip"
    python_version = "3.13"

    with TemporaryDirectory(prefix=pyship_application_name) as temp_dir:
        print(f'temp_dir="{temp_dir}"')
        version = VersionInfo.parse("0.0.1")
        application_name = "tstpyshipapp"
        app_dir = Path(temp_dir, "app")
        dist_dir = Path(temp_dir, "dist")
        cache_dir = Path(temp_dir, "cache")
        make_test_app(app_dir, application_name, version, python_version, False)  # dynamically create the test app
        app_info = AppInfo(application_name, __author__, version, False, f"https://{test_name}", test_name, False)
        clip_dir = create_clip(app_info, app_dir, dist_dir, cache_dir, python_version)
        assert Path(clip_dir, "python.exe").exists()  # make sure standalone python copied to clip root
        assert Path(clip_dir, "Lib", "site-packages", "pyship").exists()  # make sure pyship has been installed (we're using pyship itself in this test)
