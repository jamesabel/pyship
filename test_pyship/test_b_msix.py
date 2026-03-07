import struct
import zlib
from pathlib import Path
from unittest.mock import patch

import pytest
from semver import VersionInfo

from pyship import AppInfo
from pyship.msix import _find_makeappx, _msix_safe_name, _make_placeholder_png, create_msix


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_app_info(project_dir: Path) -> AppInfo:
    app_info = AppInfo()
    app_info.name = "testapp"
    app_info.author = "Test Author"
    app_info.version = VersionInfo.parse("1.2.3")
    app_info.description = "A test application"
    app_info.project_dir = project_dir
    app_info.run_on_startup = False
    app_info.is_gui = False
    return app_info


def _make_launcher_exe(app_dir: Path, app_name: str) -> Path:
    """Create a fake launcher exe so app_dir looks like a real pyship output."""
    launcher_dir = Path(app_dir, app_name)
    launcher_dir.mkdir(parents=True, exist_ok=True)
    exe = Path(launcher_dir, f"{app_name}.exe")
    exe.write_bytes(b"\x00" * 4)
    return exe


# ---------------------------------------------------------------------------
# _find_makeappx tests
# ---------------------------------------------------------------------------


def test_find_makeappx_returns_none_when_sdk_dir_missing(tmp_path):
    assert _find_makeappx(tmp_path / "nonexistent") is None


def test_find_makeappx_returns_none_when_no_version_dirs(tmp_path):
    assert _find_makeappx(tmp_path) is None


def test_find_makeappx_finds_single_version(tmp_path):
    makeappx = tmp_path / "10.0.22621.0" / "x64" / "makeappx.exe"
    makeappx.parent.mkdir(parents=True)
    makeappx.touch()
    assert _find_makeappx(tmp_path) == makeappx


def test_find_makeappx_picks_newest_version(tmp_path):
    for ver in ("10.0.19041.0", "10.0.22621.0"):
        exe = tmp_path / ver / "x64" / "makeappx.exe"
        exe.parent.mkdir(parents=True)
        exe.touch()
    assert _find_makeappx(tmp_path) == tmp_path / "10.0.22621.0" / "x64" / "makeappx.exe"


def test_find_makeappx_skips_dir_without_exe(tmp_path):
    (tmp_path / "10.0.18362.0" / "x64").mkdir(parents=True)  # no makeappx.exe here
    present = tmp_path / "10.0.19041.0" / "x64" / "makeappx.exe"
    present.parent.mkdir(parents=True)
    present.touch()
    assert _find_makeappx(tmp_path) == present


# ---------------------------------------------------------------------------
# _msix_safe_name tests
# ---------------------------------------------------------------------------


def test_msix_safe_name_replaces_spaces():
    assert " " not in _msix_safe_name("My Company")


def test_msix_safe_name_preserves_valid_chars():
    assert _msix_safe_name("MyApp-1.0_test") == "MyApp-1.0_test"


def test_msix_safe_name_strips_leading_trailing_periods():
    result = _msix_safe_name("..app..")
    assert not result.startswith(".")
    assert not result.endswith(".")


def test_msix_safe_name_empty_fallback():
    assert _msix_safe_name("...") == "App"


# ---------------------------------------------------------------------------
# _make_placeholder_png tests
# ---------------------------------------------------------------------------


def test_make_placeholder_png_starts_with_png_signature():
    png = _make_placeholder_png()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


def test_make_placeholder_png_contains_ihdr():
    png = _make_placeholder_png()
    assert b"IHDR" in png


def test_make_placeholder_png_contains_iend():
    png = _make_placeholder_png()
    assert b"IEND" in png


def test_make_placeholder_png_is_bytes():
    assert isinstance(_make_placeholder_png(), bytes)


# ---------------------------------------------------------------------------
# create_msix tests
# ---------------------------------------------------------------------------


def test_create_msix_returns_none_when_makeappx_not_found(tmp_path):
    app_info = _make_app_info(tmp_path)
    app_dir = Path(tmp_path, "app")
    app_dir.mkdir()
    _make_launcher_exe(app_dir, "testapp")

    with patch("pyship.msix._find_makeappx", return_value=None):
        result = create_msix(app_info, app_dir, "CN=Test")
    assert result is None


def test_create_msix_generates_manifest(tmp_path):
    app_info = _make_app_info(tmp_path)
    app_dir = Path(tmp_path, "app")
    app_dir.mkdir()
    _make_launcher_exe(app_dir, "testapp")
    fake_makeappx = tmp_path / "makeappx.exe"
    fake_makeappx.touch()

    with patch("pyship.msix.subprocess_run", return_value=(0, None, None)):
        # makeappx won't actually run, but manifest is written before the call
        create_msix(app_info, app_dir, "CN=Test Author, C=US", makeappx_path=fake_makeappx)

    manifest_path = Path(app_dir, "AppxManifest.xml")
    assert manifest_path.exists()
    content = manifest_path.read_text(encoding="utf-8")
    assert "testapp" in content
    assert "CN=Test Author, C=US" in content
    assert "1.2.3.0" in content
    assert "Test Author" in content
    assert "runFullTrust" in content


def test_create_msix_manifest_executable_path(tmp_path):
    app_info = _make_app_info(tmp_path)
    app_dir = Path(tmp_path, "app")
    app_dir.mkdir()
    _make_launcher_exe(app_dir, "testapp")
    fake_makeappx = tmp_path / "makeappx.exe"
    fake_makeappx.touch()

    with patch("pyship.msix.subprocess_run", return_value=(0, None, None)):
        create_msix(app_info, app_dir, "CN=Test", makeappx_path=fake_makeappx)

    content = Path(app_dir, "AppxManifest.xml").read_text(encoding="utf-8")
    assert "testapp/testapp.exe" in content


def test_create_msix_generates_placeholder_assets_when_no_store_assets_dir(tmp_path):
    app_info = _make_app_info(tmp_path)
    app_dir = Path(tmp_path, "app")
    app_dir.mkdir()
    _make_launcher_exe(app_dir, "testapp")
    fake_makeappx = tmp_path / "makeappx.exe"
    fake_makeappx.touch()

    with patch("pyship.msix.subprocess_run", return_value=(0, None, None)):
        create_msix(app_info, app_dir, "CN=Test", makeappx_path=fake_makeappx)

    assets_dir = Path(app_dir, "assets")
    for asset_name in ("StoreLogo.png", "Square44x44Logo.png", "Square150x150Logo.png"):
        asset = Path(assets_dir, asset_name)
        assert asset.exists(), f"missing placeholder asset: {asset_name}"
        assert asset.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


def test_create_msix_copies_store_assets_when_provided(tmp_path):
    app_info = _make_app_info(tmp_path)
    app_dir = Path(tmp_path, "app")
    app_dir.mkdir()
    _make_launcher_exe(app_dir, "testapp")
    fake_makeappx = tmp_path / "makeappx.exe"
    fake_makeappx.touch()

    store_assets = tmp_path / "store_assets"
    store_assets.mkdir()
    sentinel = b"\x89PNG\r\n\x1a\nSENTINEL"
    for name in ("StoreLogo.png", "Square44x44Logo.png", "Square150x150Logo.png"):
        Path(store_assets, name).write_bytes(sentinel)

    with patch("pyship.msix.subprocess_run", return_value=(0, None, None)):
        create_msix(app_info, app_dir, "CN=Test", store_assets_dir=store_assets, makeappx_path=fake_makeappx)

    for name in ("StoreLogo.png", "Square44x44Logo.png", "Square150x150Logo.png"):
        assert Path(app_dir, "assets", name).read_bytes() == sentinel


def test_create_msix_calls_makeappx_with_correct_flags(tmp_path):
    app_info = _make_app_info(tmp_path)
    app_dir = Path(tmp_path, "app")
    app_dir.mkdir()
    _make_launcher_exe(app_dir, "testapp")
    fake_makeappx = tmp_path / "makeappx.exe"
    fake_makeappx.touch()

    with patch("pyship.msix.subprocess_run", return_value=(0, None, None)) as mock_run:
        create_msix(app_info, app_dir, "CN=Test", makeappx_path=fake_makeappx)

    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "pack" in cmd
    assert "/d" in cmd
    assert "/p" in cmd
    assert "/o" in cmd
    assert str(app_dir) in cmd


def test_create_msix_returns_none_on_nonzero_return_code(tmp_path):
    app_info = _make_app_info(tmp_path)
    app_dir = Path(tmp_path, "app")
    app_dir.mkdir()
    _make_launcher_exe(app_dir, "testapp")
    fake_makeappx = tmp_path / "makeappx.exe"
    fake_makeappx.touch()

    with patch("pyship.msix.subprocess_run", return_value=(1, None, None)):
        result = create_msix(app_info, app_dir, "CN=Test", makeappx_path=fake_makeappx)
    assert result is None


def test_create_msix_returns_path_on_success(tmp_path):
    app_info = _make_app_info(tmp_path)
    app_dir = Path(tmp_path, "app")
    app_dir.mkdir()
    _make_launcher_exe(app_dir, "testapp")
    fake_makeappx = tmp_path / "makeappx.exe"
    fake_makeappx.touch()

    def fake_subprocess_run(cmd, *args, **kwargs):
        # Actually create the output file so exists() check passes
        for i, arg in enumerate(cmd):
            if arg == "/p" and i + 1 < len(cmd):
                Path(cmd[i + 1]).touch()
        return (0, None, None)

    with patch("pyship.msix.subprocess_run", side_effect=fake_subprocess_run):
        result = create_msix(app_info, app_dir, "CN=Test", makeappx_path=fake_makeappx)

    assert result is not None
    assert result.suffix == ".msix"
    assert "testapp" in result.name


def test_create_msix_output_in_installers_dir(tmp_path):
    app_info = _make_app_info(tmp_path)
    app_dir = Path(tmp_path, "app")
    app_dir.mkdir()
    _make_launcher_exe(app_dir, "testapp")
    fake_makeappx = tmp_path / "makeappx.exe"
    fake_makeappx.touch()

    def fake_subprocess_run(cmd, *args, **kwargs):
        for i, arg in enumerate(cmd):
            if arg == "/p" and i + 1 < len(cmd):
                Path(cmd[i + 1]).touch()
        return (0, None, None)

    with patch("pyship.msix.subprocess_run", side_effect=fake_subprocess_run):
        result = create_msix(app_info, app_dir, "CN=Test", makeappx_path=fake_makeappx)

    assert result is not None
    assert result.parent.name == "installers"
    assert result.parent.parent == tmp_path
