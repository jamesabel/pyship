from pprint import pprint

from semver import VersionInfo
from balsa import get_logger

from pyship import PyShip, CLIP_EXT
from pyship.constants import is_ci
from pyship.main import read_pyship_config
from test_pyship import TstAppDirs, TST_APP_NAME

log = get_logger(TST_APP_NAME)


def test_cloud():
    # Moto mock is enabled in conftest.py session fixture
    version = VersionInfo.parse("0.0.1")
    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
    py_ship = PyShip(tst_app_dirs.project_dir, dist_dir=tst_app_dirs.dist_dir)
    py_ship.cloud_bucket = "testawsimple"  # awsimple moto mock creates this on demand
    py_ship.cloud_profile = "default"  # with moto mock we don't need a real profile
    log.info(f"{py_ship.cloud_profile=}")
    installer_path = py_ship.ship()

    # In CI, NSIS may not be available so installer won't be created
    if installer_path is not None:
        uploaded_files = py_ship.cloud_access.s3_access.dir()
        pprint(uploaded_files)
        clip_file_name = f"{TST_APP_NAME}_{version}.{CLIP_EXT}"
        assert clip_file_name in uploaded_files
        installer_name = f"{TST_APP_NAME}_installer_win64.exe"
        assert installer_name in uploaded_files
    else:
        assert is_ci(), "Installer creation failed but not running in CI"
        log.info("Skipping upload assertions - NSIS not available in CI")


def test_cloud_public_readable():
    # Verify that public_readable flag propagates to s3_access
    version = VersionInfo.parse("0.0.1")
    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
    py_ship = PyShip(tst_app_dirs.project_dir, dist_dir=tst_app_dirs.dist_dir)
    py_ship.cloud_bucket = "testawsimple"
    py_ship.cloud_profile = "default"
    py_ship.public_readable = True
    installer_path = py_ship.ship()

    if installer_path is not None:
        assert py_ship.cloud_access is not None
        assert py_ship.cloud_access.s3_access.public_readable is True
    else:
        assert is_ci(), "Installer creation failed but not running in CI"
        log.info("Skipping public_readable assertions - NSIS not available in CI")


def test_read_pyship_config(tmp_path, monkeypatch):
    """Test that read_pyship_config reads [tool.pyship] settings from pyproject.toml."""
    pyproject_content = """\
[project]
name = "myapp"

[tool.pyship]
name = "myapp"
profile = "myprofile"
upload = false
public_readable = true
dist = "output"
"""
    pyproject_path = tmp_path / "pyproject.toml"
    pyproject_path.write_text(pyproject_content)
    monkeypatch.chdir(tmp_path)

    config = read_pyship_config()
    assert config["name"] == "myapp"
    assert config["profile"] == "myprofile"
    assert config["upload"] is False
    assert config["public_readable"] is True
    assert config["dist"] == "output"


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
