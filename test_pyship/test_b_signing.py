from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pyship.signing import _find_signtool, sign_file, sign_if_configured


# ---------------------------------------------------------------------------
# _find_signtool tests
# ---------------------------------------------------------------------------


def test_find_signtool_returns_none_when_sdk_dir_missing(tmp_path):
    missing = tmp_path / "nonexistent"
    assert _find_signtool(missing) is None


def test_find_signtool_returns_none_when_no_version_dirs(tmp_path):
    # empty dir — no subdirectories at all
    assert _find_signtool(tmp_path) is None


def test_find_signtool_finds_single_version(tmp_path):
    ver_dir = tmp_path / "10.0.22621.0"
    signtool = ver_dir / "x64" / "signtool.exe"
    signtool.parent.mkdir(parents=True)
    signtool.touch()

    result = _find_signtool(tmp_path)
    assert result == signtool


def test_find_signtool_picks_newest_of_multiple_versions(tmp_path):
    for ver in ("10.0.19041.0", "10.0.22621.0"):
        signtool = tmp_path / ver / "x64" / "signtool.exe"
        signtool.parent.mkdir(parents=True)
        signtool.touch()

    result = _find_signtool(tmp_path)
    assert result == tmp_path / "10.0.22621.0" / "x64" / "signtool.exe"


def test_find_signtool_skips_version_dir_without_signtool_exe(tmp_path):
    # dir without signtool.exe
    (tmp_path / "10.0.18362.0" / "x64").mkdir(parents=True)
    # dir with signtool.exe
    present = tmp_path / "10.0.19041.0" / "x64" / "signtool.exe"
    present.parent.mkdir(parents=True)
    present.touch()

    result = _find_signtool(tmp_path)
    assert result == present


# ---------------------------------------------------------------------------
# sign_if_configured skip tests
# ---------------------------------------------------------------------------


def test_sign_if_configured_skips_when_file_path_none(tmp_path):
    pfx = tmp_path / "cert.pfx"
    pfx.touch()
    result = sign_if_configured(None, pfx, "password", "http://timestamp.example.com")
    assert result is False


def test_sign_if_configured_skips_when_pfx_path_none(tmp_path):
    target = tmp_path / "app.exe"
    target.touch()
    result = sign_if_configured(target, None, "password", "http://timestamp.example.com")
    assert result is False


def test_sign_if_configured_skips_when_password_none(tmp_path):
    target = tmp_path / "app.exe"
    target.touch()
    pfx = tmp_path / "cert.pfx"
    pfx.touch()
    result = sign_if_configured(target, pfx, None, "http://timestamp.example.com")
    assert result is False


# ---------------------------------------------------------------------------
# sign_file tests
# ---------------------------------------------------------------------------


def test_sign_file_returns_false_when_signtool_not_found(tmp_path):
    target = tmp_path / "app.exe"
    target.touch()
    pfx = tmp_path / "cert.pfx"
    pfx.touch()

    with patch("pyship.signing._find_signtool", return_value=None):
        result = sign_file(target, pfx, "password", "http://timestamp.example.com")
    assert result is False


def test_sign_file_returns_false_when_file_missing(tmp_path):
    missing = tmp_path / "missing.exe"
    pfx = tmp_path / "cert.pfx"
    pfx.touch()
    signtool = tmp_path / "signtool.exe"
    signtool.touch()

    result = sign_file(missing, pfx, "password", "http://timestamp.example.com", signtool_path=signtool)
    assert result is False


def test_sign_file_returns_false_when_pfx_missing(tmp_path):
    target = tmp_path / "app.exe"
    target.touch()
    missing_pfx = tmp_path / "missing.pfx"
    signtool = tmp_path / "signtool.exe"
    signtool.touch()

    result = sign_file(target, missing_pfx, "password", "http://timestamp.example.com", signtool_path=signtool)
    assert result is False


def test_sign_file_calls_subprocess_with_correct_args(tmp_path):
    target = tmp_path / "app.exe"
    target.touch()
    pfx = tmp_path / "cert.pfx"
    pfx.touch()
    signtool = tmp_path / "signtool.exe"
    signtool.touch()

    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)) as mock_run:
        result = sign_file(target, pfx, "secret", "http://timestamp.digicert.com", signtool_path=signtool)

    assert result is True
    mock_run.assert_called_once()
    cmd = mock_run.call_args[0][0]
    assert "/f" in cmd
    assert "/p" in cmd
    assert "/tr" in cmd
    assert "sha256" in cmd
    assert "/fd" in cmd
    assert str(target) in cmd
    assert str(pfx) in cmd
    assert "secret" in cmd


def test_sign_file_returns_false_on_nonzero_return_code(tmp_path):
    target = tmp_path / "app.exe"
    target.touch()
    pfx = tmp_path / "cert.pfx"
    pfx.touch()
    signtool = tmp_path / "signtool.exe"
    signtool.touch()

    with patch("pyship.signing.subprocess_run", return_value=(1, None, None)):
        result = sign_file(target, pfx, "password", "http://timestamp.example.com", signtool_path=signtool)
    assert result is False


def test_sign_file_returns_true_on_success(tmp_path):
    target = tmp_path / "app.exe"
    target.touch()
    pfx = tmp_path / "cert.pfx"
    pfx.touch()
    signtool = tmp_path / "signtool.exe"
    signtool.touch()

    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)):
        result = sign_file(target, pfx, "password", "http://timestamp.example.com", signtool_path=signtool)
    assert result is True


# ---------------------------------------------------------------------------
# create_pyship_launcher return type test
# ---------------------------------------------------------------------------


def test_create_pyship_launcher_returns_none_when_name_is_none(tmp_path):
    from pyship import AppInfo
    from pyship.create_launcher import create_pyship_launcher

    app_info = AppInfo()
    app_info.name = None  # trigger the early-return path

    result = create_pyship_launcher(app_info, tmp_path)
    assert result is None
