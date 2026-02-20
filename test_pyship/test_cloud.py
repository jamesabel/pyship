from pprint import pprint
from pathlib import Path
from tempfile import TemporaryDirectory

from semver import VersionInfo

from pyship import PyShip, CLIP_EXT
from pyship.ci import is_ci
from pyship.main import read_pyship_config
from pyship import __application_name__ as pyship_application_name

from .make_test_app import make_test_app


def test_cloud():
    # Moto mock is enabled in conftest.py session fixture

    with TemporaryDirectory(prefix=pyship_application_name) as temp_dir:
        print(f'temp_dir="{temp_dir}"')
        version = VersionInfo.parse("0.0.1")
        minimum_python_version = "3.14"
        application_name = "tstpyshipapp"
        project_dir = Path(temp_dir, "project")
        make_test_app(project_dir, application_name, version, minimum_python_version, False)  # dynamically create the test app
        py_ship = PyShip(project_dir, cloud_bucket="testpyship", python_version=minimum_python_version)
        installer_path = py_ship.ship()

        # In CI, NSIS may not be available so installer won't be created
        if installer_path is None:
            assert is_ci(), "Installer creation failed but not running in CI"
            print("Skipping upload assertions - NSIS not available in CI")
        else:
            # todo: check the upload
            pass
            # uploaded_files = py_ship.cloud_access.s3_access.dir()
            # pprint(uploaded_files)
            # clip_file_name = f"{application_name}_{version}.{CLIP_EXT}"
            # assert clip_file_name in uploaded_files
            # installer_name = f"{application_name}_installer_win64.exe"
            # assert installer_name in uploaded_files


def test_read_pyship_config(tmp_path, monkeypatch):
    """Test that read_pyship_config reads [tool.pyship] settings from pyproject.toml."""
    pyproject_content = """\
[project]
name = "myapp"

[tool.pyship]
profile = "myprofile"
upload = false
public_readable = true
"""
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(pyproject_content)
    monkeypatch.chdir(tmp_path)

    config = read_pyship_config()
    assert config["profile"] == "myprofile"
    assert config["upload"] is False
    assert config["public_readable"] is True


def test_read_pyship_config_empty(tmp_path, monkeypatch):
    """Test that read_pyship_config returns empty dict when no [tool.pyship] section exists."""
    pyproject_content = """\
[project]
name = "myapp"
"""
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(pyproject_content)
    monkeypatch.chdir(tmp_path)

    config = read_pyship_config()
    assert config == {}


def test_read_pyship_config_no_file(tmp_path, monkeypatch):
    """Test that read_pyship_config returns empty dict when no pyproject.toml exists."""
    monkeypatch.chdir(tmp_path)
    config = read_pyship_config()
    assert config == {}
