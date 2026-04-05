"""Tests for pyship.signing — signtool discovery, PFX signing, token signing, and pre-flight detection."""

import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pyship.signing import (
    _find_signtool,
    _resolve_signtool,
    _run_signtool,
    _validate_sha1,
    check_signing_available,
    is_certificate_in_store,
    is_token_present,
    sign_file,
    sign_file_token,
    sign_if_configured,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def target_exe(tmp_path):
    """Create a dummy .exe file to sign."""
    exe = tmp_path / "app.exe"
    exe.touch()
    return exe


@pytest.fixture()
def pfx_file(tmp_path):
    """Create a dummy .pfx certificate file."""
    pfx = tmp_path / "cert.pfx"
    pfx.touch()
    return pfx


@pytest.fixture()
def signtool_exe(tmp_path):
    """Create a dummy signtool.exe."""
    st = tmp_path / "signtool.exe"
    st.touch()
    return st


TIMESTAMP_URL = "http://timestamp.example.com"
VALID_SHA1 = "aa" * 20  # 40-char hex


# ---------------------------------------------------------------------------
# _find_signtool
# ---------------------------------------------------------------------------


def test_find_signtool_returns_none_when_sdk_dir_missing(tmp_path):
    assert _find_signtool(tmp_path / "nonexistent") is None


def test_find_signtool_returns_none_when_no_version_dirs(tmp_path):
    assert _find_signtool(tmp_path) is None


def test_find_signtool_finds_single_version(tmp_path):
    signtool = tmp_path / "10.0.22621.0" / "x64" / "signtool.exe"
    signtool.parent.mkdir(parents=True)
    signtool.touch()
    assert _find_signtool(tmp_path) == signtool


def test_find_signtool_picks_newest_of_multiple_versions(tmp_path):
    for ver in ("10.0.19041.0", "10.0.22621.0"):
        st = tmp_path / ver / "x64" / "signtool.exe"
        st.parent.mkdir(parents=True)
        st.touch()
    assert _find_signtool(tmp_path) == tmp_path / "10.0.22621.0" / "x64" / "signtool.exe"


def test_find_signtool_skips_version_dir_without_signtool_exe(tmp_path):
    (tmp_path / "10.0.18362.0" / "x64").mkdir(parents=True)
    present = tmp_path / "10.0.19041.0" / "x64" / "signtool.exe"
    present.parent.mkdir(parents=True)
    present.touch()
    assert _find_signtool(tmp_path) == present


# ---------------------------------------------------------------------------
# _resolve_signtool
# ---------------------------------------------------------------------------


def test_resolve_signtool_passes_through_explicit_path(signtool_exe):
    assert _resolve_signtool(signtool_exe) == signtool_exe


def test_resolve_signtool_returns_none_when_not_found():
    with patch("pyship.signing._find_signtool", return_value=None):
        assert _resolve_signtool(None) is None


# ---------------------------------------------------------------------------
# _run_signtool
# ---------------------------------------------------------------------------


def test_run_signtool_returns_true_on_success(target_exe):
    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)):
        assert _run_signtool(["signtool", "sign", str(target_exe)], target_exe) is True


def test_run_signtool_returns_false_on_failure(target_exe):
    with patch("pyship.signing.subprocess_run", return_value=(1, None, None)):
        assert _run_signtool(["signtool", "sign", str(target_exe)], target_exe) is False


# ---------------------------------------------------------------------------
# _validate_sha1
# ---------------------------------------------------------------------------


def test_validate_sha1_valid():
    assert _validate_sha1("AA BB CC " + "dd" * 17) == "AABBCC" + "dd" * 17


def test_validate_sha1_too_short():
    assert _validate_sha1("aabb") is None


def test_validate_sha1_non_hex():
    assert _validate_sha1("zz" * 20) is None


# ---------------------------------------------------------------------------
# sign_if_configured — PFX skip tests
# ---------------------------------------------------------------------------


def test_sign_if_configured_skips_when_file_path_none(pfx_file):
    assert sign_if_configured(None, pfx_file, "password", TIMESTAMP_URL) is False


def test_sign_if_configured_skips_when_pfx_path_none(target_exe):
    assert sign_if_configured(target_exe, None, "password", TIMESTAMP_URL) is False


def test_sign_if_configured_skips_when_password_none(target_exe, pfx_file):
    assert sign_if_configured(target_exe, pfx_file, None, TIMESTAMP_URL) is False


# ---------------------------------------------------------------------------
# sign_file — PFX mode
# ---------------------------------------------------------------------------


def test_sign_file_returns_false_when_signtool_not_found(target_exe, pfx_file):
    with patch("pyship.signing._find_signtool", return_value=None):
        assert sign_file(target_exe, pfx_file, "password", TIMESTAMP_URL) is False


def test_sign_file_returns_false_when_file_missing(tmp_path, pfx_file, signtool_exe):
    assert sign_file(tmp_path / "missing.exe", pfx_file, "password", TIMESTAMP_URL, signtool_path=signtool_exe) is False


def test_sign_file_returns_false_when_pfx_missing(target_exe, tmp_path, signtool_exe):
    assert sign_file(target_exe, tmp_path / "missing.pfx", "password", TIMESTAMP_URL, signtool_path=signtool_exe) is False


def test_sign_file_calls_subprocess_with_correct_args(target_exe, pfx_file, signtool_exe):
    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)) as mock_run:
        assert sign_file(target_exe, pfx_file, "secret", "http://timestamp.digicert.com", signtool_path=signtool_exe) is True

    cmd = mock_run.call_args[0][0]
    assert "/f" in cmd
    assert "/p" in cmd
    assert "/tr" in cmd
    assert "/fd" in cmd
    assert "sha256" in cmd
    assert str(target_exe) in cmd
    assert str(pfx_file) in cmd
    assert "secret" in cmd


def test_sign_file_returns_false_on_nonzero_return_code(target_exe, pfx_file, signtool_exe):
    with patch("pyship.signing.subprocess_run", return_value=(1, None, None)):
        assert sign_file(target_exe, pfx_file, "password", TIMESTAMP_URL, signtool_path=signtool_exe) is False


def test_sign_file_returns_true_on_success(target_exe, pfx_file, signtool_exe):
    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)):
        assert sign_file(target_exe, pfx_file, "password", TIMESTAMP_URL, signtool_path=signtool_exe) is True


# ---------------------------------------------------------------------------
# create_pyship_launcher return type test
# ---------------------------------------------------------------------------


def test_create_pyship_launcher_returns_none_when_name_is_none(tmp_path):
    from pyship import AppInfo
    from pyship.create_launcher import create_pyship_launcher

    app_info = AppInfo()
    app_info.name = None
    assert create_pyship_launcher(app_info, tmp_path) is None


# ---------------------------------------------------------------------------
# is_token_present
# ---------------------------------------------------------------------------


_SMARTCARD_OUTPUT = """\
Status Class     FriendlyName
------ -----     ------------
OK     SmartCard SafeNet IDPrime MD Smart Card
"""


def _mock_pnp_result(returncode: int, stdout: str) -> MagicMock:
    """Create a mock subprocess.CompletedProcess for PnP queries."""
    mock = MagicMock()
    mock.returncode = returncode
    mock.stdout = stdout
    return mock


def test_is_token_present_returns_true_when_smartcard_found():
    with patch("pyship.signing.subprocess.run", return_value=_mock_pnp_result(0, _SMARTCARD_OUTPUT)):
        assert is_token_present() is True


def test_is_token_present_returns_false_when_no_devices():
    with patch("pyship.signing.subprocess.run", return_value=_mock_pnp_result(0, "")):
        assert is_token_present() is False


def test_is_token_present_returns_false_on_command_failure():
    with patch("pyship.signing.subprocess.run", return_value=_mock_pnp_result(1, "")):
        assert is_token_present() is False


def test_is_token_present_returns_false_on_exception():
    with patch("pyship.signing.subprocess.run", side_effect=OSError("not found")):
        assert is_token_present() is False


# ---------------------------------------------------------------------------
# is_certificate_in_store
# ---------------------------------------------------------------------------


def _mock_cert_store(cert_der: bytes):
    """Return a mock cert list suitable for patching ssl.enum_certificates."""
    return [(cert_der, "x509_asn", set())]


def test_is_certificate_in_store_finds_by_sha1():
    cert_der = b"test cert data"
    thumbprint = hashlib.sha1(cert_der).hexdigest()
    with patch("pyship.signing.ssl.enum_certificates", return_value=_mock_cert_store(cert_der)):
        assert is_certificate_in_store(certificate_sha1=thumbprint) is True


def test_is_certificate_in_store_sha1_not_found():
    with patch("pyship.signing.ssl.enum_certificates", return_value=_mock_cert_store(b"cert")):
        assert is_certificate_in_store(certificate_sha1=VALID_SHA1) is False


def test_is_certificate_in_store_finds_by_subject():
    with patch("pyship.signing.ssl.enum_certificates", return_value=_mock_cert_store(b"CN=My Company, O=My Company LLC")):
        assert is_certificate_in_store(certificate_subject="My Company") is True


def test_is_certificate_in_store_subject_not_found():
    with patch("pyship.signing.ssl.enum_certificates", return_value=_mock_cert_store(b"CN=Other Corp")):
        assert is_certificate_in_store(certificate_subject="My Company") is False


def test_is_certificate_in_store_returns_false_when_no_args():
    assert is_certificate_in_store() is False


def test_is_certificate_in_store_returns_false_on_exception():
    with patch("pyship.signing.ssl.enum_certificates", side_effect=OSError("unavailable")):
        assert is_certificate_in_store(certificate_sha1=VALID_SHA1) is False


# ---------------------------------------------------------------------------
# check_signing_available
# ---------------------------------------------------------------------------


def test_check_signing_available_pfx_exists(pfx_file):
    assert check_signing_available(pfx_path=pfx_file) is True


def test_check_signing_available_pfx_missing(tmp_path):
    assert check_signing_available(pfx_path=tmp_path / "missing.pfx") is False


def test_check_signing_available_token_mode_both_checks_pass():
    with patch("pyship.signing.is_token_present", return_value=True), patch("pyship.signing.is_certificate_in_store", return_value=True):
        assert check_signing_available(certificate_sha1=VALID_SHA1) is True


def test_check_signing_available_token_not_present():
    with patch("pyship.signing.is_token_present", return_value=False):
        assert check_signing_available(certificate_sha1=VALID_SHA1) is False


def test_check_signing_available_token_present_cert_missing():
    with patch("pyship.signing.is_token_present", return_value=True), patch("pyship.signing.is_certificate_in_store", return_value=False):
        assert check_signing_available(certificate_sha1=VALID_SHA1) is False


def test_check_signing_available_auto_select_token_present():
    with patch("pyship.signing.is_token_present", return_value=True):
        assert check_signing_available(certificate_auto_select=True) is True


def test_check_signing_available_nothing_configured():
    assert check_signing_available() is False


# ---------------------------------------------------------------------------
# sign_file_token
# ---------------------------------------------------------------------------


def test_sign_file_token_returns_false_when_signtool_not_found(target_exe):
    with patch("pyship.signing._find_signtool", return_value=None):
        assert sign_file_token(target_exe, TIMESTAMP_URL, certificate_sha1=VALID_SHA1) is False


def test_sign_file_token_returns_false_when_file_missing(tmp_path, signtool_exe):
    assert sign_file_token(tmp_path / "missing.exe", TIMESTAMP_URL, certificate_sha1=VALID_SHA1, signtool_path=signtool_exe) is False


def test_sign_file_token_sha1_builds_correct_command(target_exe, signtool_exe):
    thumbprint = "AABB" * 10
    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)) as mock_run:
        assert sign_file_token(target_exe, "http://timestamp.digicert.com", certificate_sha1=thumbprint, signtool_path=signtool_exe) is True

    cmd = mock_run.call_args[0][0]
    assert "/sha1" in cmd
    assert thumbprint.lower() in [c.lower() for c in cmd]
    assert "/f" not in cmd
    assert "/tr" in cmd
    assert "/td" in cmd
    assert "/fd" in cmd


def test_sign_file_token_subject_builds_correct_command(target_exe, signtool_exe):
    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)) as mock_run:
        assert sign_file_token(target_exe, "http://timestamp.digicert.com", certificate_subject="My Company", signtool_path=signtool_exe) is True

    cmd = mock_run.call_args[0][0]
    assert "/n" in cmd
    assert "My Company" in cmd
    assert "/sha1" not in cmd
    assert "/f" not in cmd


def test_sign_file_token_auto_select_builds_correct_command(target_exe, signtool_exe):
    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)) as mock_run:
        assert sign_file_token(target_exe, "http://timestamp.digicert.com", certificate_auto_select=True, signtool_path=signtool_exe) is True

    cmd = mock_run.call_args[0][0]
    assert "/a" in cmd
    assert "/sha1" not in cmd
    assert "/n" not in cmd
    assert "/f" not in cmd


def test_sign_file_token_with_pin_includes_p_flag(target_exe, signtool_exe):
    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)) as mock_run:
        sign_file_token(target_exe, "http://timestamp.digicert.com", certificate_sha1=VALID_SHA1, token_pin="123456", signtool_path=signtool_exe)

    cmd = mock_run.call_args[0][0]
    assert "/p" in cmd
    assert "123456" in cmd


def test_sign_file_token_without_pin_excludes_p_flag(target_exe, signtool_exe):
    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)) as mock_run:
        sign_file_token(target_exe, "http://timestamp.digicert.com", certificate_sha1=VALID_SHA1, signtool_path=signtool_exe)

    assert "/p" not in mock_run.call_args[0][0]


def test_sign_file_token_with_csp_and_kc(target_exe, signtool_exe):
    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)) as mock_run:
        sign_file_token(
            target_exe,
            "http://timestamp.digicert.com",
            certificate_sha1=VALID_SHA1,
            certificate_csp="eToken Base Cryptographic Provider",
            certificate_key_container="my-container",
            signtool_path=signtool_exe,
        )

    cmd = mock_run.call_args[0][0]
    assert "/csp" in cmd
    assert "eToken Base Cryptographic Provider" in cmd
    assert "/kc" in cmd
    assert "my-container" in cmd


def test_sign_file_token_invalid_sha1_returns_false(target_exe, signtool_exe):
    assert sign_file_token(target_exe, TIMESTAMP_URL, certificate_sha1="not_hex", signtool_path=signtool_exe) is False


def test_sign_file_token_short_sha1_returns_false(target_exe, signtool_exe):
    assert sign_file_token(target_exe, TIMESTAMP_URL, certificate_sha1="aabb", signtool_path=signtool_exe) is False


def test_sign_file_token_multiple_selectors_returns_false(target_exe, signtool_exe):
    assert sign_file_token(target_exe, TIMESTAMP_URL, certificate_sha1=VALID_SHA1, certificate_subject="My Co", signtool_path=signtool_exe) is False


def test_sign_file_token_no_selector_returns_false(target_exe, signtool_exe):
    assert sign_file_token(target_exe, TIMESTAMP_URL, signtool_path=signtool_exe) is False


def test_sign_file_token_returns_true_on_success(target_exe, signtool_exe):
    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)):
        assert sign_file_token(target_exe, TIMESTAMP_URL, certificate_sha1=VALID_SHA1, signtool_path=signtool_exe) is True


def test_sign_file_token_returns_false_on_nonzero_return_code(target_exe, signtool_exe):
    with patch("pyship.signing.subprocess_run", return_value=(1, None, None)):
        assert sign_file_token(target_exe, TIMESTAMP_URL, certificate_sha1=VALID_SHA1, signtool_path=signtool_exe) is False


# ---------------------------------------------------------------------------
# sign_if_configured — token mode dispatch
# ---------------------------------------------------------------------------


def test_sign_if_configured_dispatches_to_token_mode_sha1(target_exe):
    with patch("pyship.signing.sign_file_token", return_value=True) as mock_token:
        assert sign_if_configured(target_exe, None, "pin123", TIMESTAMP_URL, certificate_sha1=VALID_SHA1) is True

    mock_token.assert_called_once()
    assert mock_token.call_args.kwargs["certificate_sha1"] == VALID_SHA1
    assert mock_token.call_args.kwargs["token_pin"] == "pin123"


def test_sign_if_configured_dispatches_to_token_mode_subject(target_exe):
    with patch("pyship.signing.sign_file_token", return_value=True) as mock_token:
        assert sign_if_configured(target_exe, None, None, TIMESTAMP_URL, certificate_subject="My Company") is True

    mock_token.assert_called_once()
    assert mock_token.call_args.kwargs["certificate_subject"] == "My Company"
    assert mock_token.call_args.kwargs["token_pin"] is None


def test_sign_if_configured_dispatches_to_token_mode_auto(target_exe):
    with patch("pyship.signing.sign_file_token", return_value=True) as mock_token:
        assert sign_if_configured(target_exe, None, None, TIMESTAMP_URL, certificate_auto_select=True) is True

    mock_token.assert_called_once()
    assert mock_token.call_args.kwargs["certificate_auto_select"] is True


def test_sign_if_configured_returns_false_when_both_modes_configured(target_exe, pfx_file):
    assert sign_if_configured(target_exe, pfx_file, "password", TIMESTAMP_URL, certificate_sha1=VALID_SHA1) is False


def test_sign_if_configured_token_mode_without_pin(target_exe):
    with patch("pyship.signing.sign_file_token", return_value=True) as mock_token:
        assert sign_if_configured(target_exe, None, None, TIMESTAMP_URL, certificate_sha1=VALID_SHA1) is True

    assert mock_token.call_args.kwargs["token_pin"] is None


def test_sign_if_configured_no_signing_configured(target_exe):
    assert sign_if_configured(target_exe, None, None, TIMESTAMP_URL) is False
