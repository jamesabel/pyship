"""Additional tests to improve code coverage for pyship.signing, pyship.pyship, pyship.main, and pyship.arguments."""

import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock
from argparse import Namespace

import pytest

from pyship.signing import is_certificate_in_store, sign_if_configured
from pyship.pyship import PyShip, SIGNING_PIN_ENV_VAR
from pyship.exceptions import PyshipSigningUnavailable
from pyship.main import read_pyship_config
from pyship.arguments import get_arguments


# ---------------------------------------------------------------------------
# signing.py — is_certificate_in_store branch coverage
# ---------------------------------------------------------------------------


def test_is_certificate_in_store_skips_non_x509_encoding():
    """Cert with non-x509 encoding_type should be skipped."""
    cert_der = b"test cert data"
    thumbprint = hashlib.sha1(cert_der).hexdigest()
    # encoding_type is "pkcs_7_asn" instead of "x509_asn" — should be skipped
    with patch("pyship.signing.ssl.enum_certificates", return_value=[(cert_der, "pkcs_7_asn", set())]):
        assert is_certificate_in_store(certificate_sha1=thumbprint) is False


def test_is_certificate_in_store_both_sha1_and_subject():
    """When both sha1 and subject are provided, either match should succeed."""
    cert_der = b"CN=My Company"
    thumbprint = hashlib.sha1(cert_der).hexdigest()
    with patch("pyship.signing.ssl.enum_certificates", return_value=[(cert_der, "x509_asn", set())]):
        assert is_certificate_in_store(certificate_sha1=thumbprint, certificate_subject="My Company") is True


def test_is_certificate_in_store_sha1_miss_subject_hit():
    """SHA1 doesn't match but subject does."""
    cert_der = b"CN=My Company"
    with patch("pyship.signing.ssl.enum_certificates", return_value=[(cert_der, "x509_asn", set())]):
        assert is_certificate_in_store(certificate_sha1="bb" * 20, certificate_subject="My Company") is True


# ---------------------------------------------------------------------------
# signing.py — sign_if_configured PFX mode dispatches to sign_file
# ---------------------------------------------------------------------------


def test_sign_if_configured_pfx_mode_calls_sign_file(tmp_path):
    """When pfx_path is set and password provided, sign_file should be called."""
    target = tmp_path / "app.exe"
    target.touch()
    pfx = tmp_path / "cert.pfx"
    pfx.touch()

    with patch("pyship.signing.sign_file", return_value=True) as mock_sign:
        result = sign_if_configured(target, pfx, "secret", "http://ts.example.com")

    assert result is True
    mock_sign.assert_called_once()


# ---------------------------------------------------------------------------
# pyship.py — _resolve_password
# ---------------------------------------------------------------------------


def test_resolve_password_explicit_takes_priority(monkeypatch):
    """Explicit certificate_password should take priority over env var."""
    monkeypatch.setenv(SIGNING_PIN_ENV_VAR, "from_env")
    ps = PyShip(certificate_password="explicit")
    assert ps._resolve_password() == "explicit"


def test_resolve_password_falls_back_to_env_var(monkeypatch):
    """When certificate_password is None, should read from PYSHIP_SIGNING_CERTIFICATE_PIN."""
    monkeypatch.setenv(SIGNING_PIN_ENV_VAR, "env_pin")
    ps = PyShip()
    assert ps._resolve_password() == "env_pin"


def test_resolve_password_returns_none_when_nothing_set(monkeypatch):
    """When neither explicit nor env var set, should return None."""
    monkeypatch.delenv(SIGNING_PIN_ENV_VAR, raising=False)
    ps = PyShip()
    assert ps._resolve_password() is None


# ---------------------------------------------------------------------------
# pyship.py — _sign_or_raise
# ---------------------------------------------------------------------------


def test_sign_or_raise_succeeds(tmp_path):
    """When sign_if_configured returns True, no exception should be raised."""
    target = tmp_path / "app.exe"
    target.touch()
    ps = PyShip()

    with patch("pyship.pyship.sign_if_configured", return_value=True):
        ps._sign_or_raise(target, "password")  # should not raise


def test_sign_or_raise_raises_on_failure(tmp_path):
    """When sign_if_configured returns False, PyshipSigningUnavailable should be raised."""
    target = tmp_path / "app.exe"
    target.touch()
    ps = PyShip()

    with patch("pyship.pyship.sign_if_configured", return_value=False):
        with pytest.raises(PyshipSigningUnavailable):
            ps._sign_or_raise(target, "password")


# ---------------------------------------------------------------------------
# main.py — read_pyship_config with signing keys
# ---------------------------------------------------------------------------


def test_read_pyship_config_reads_signing_keys(tmp_path, monkeypatch):
    """read_pyship_config should read code_sign, certificate_sha1, etc."""
    pyproject_content = """\
[project]
name = "myapp"

[tool.pyship]
code_sign = true
certificate_sha1 = "aabbccdd"
certificate_auto_select = false
"""
    (tmp_path / "pyproject.toml").write_text(pyproject_content)
    monkeypatch.chdir(tmp_path)

    config = read_pyship_config()
    assert config["code_sign"] is True
    assert config["certificate_sha1"] == "aabbccdd"
    assert config["certificate_auto_select"] is False


def test_read_pyship_config_ignores_appinfo_keys(tmp_path, monkeypatch):
    """AppInfo-level keys like ui and run_on_startup should not be in config."""
    pyproject_content = """\
[project]
name = "myapp"

[tool.pyship]
ui = "gui"
run_on_startup = true
upload = false
"""
    (tmp_path / "pyproject.toml").write_text(pyproject_content)
    monkeypatch.chdir(tmp_path)

    config = read_pyship_config()
    assert "ui" not in config
    assert "run_on_startup" not in config
    assert config["upload"] is False


# ---------------------------------------------------------------------------
# arguments.py — get_arguments
# ---------------------------------------------------------------------------


def test_get_arguments_defaults(monkeypatch):
    """Default args should have signing fields as None/False."""
    monkeypatch.setattr("sys.argv", ["pyship"])
    args = get_arguments()
    assert args.pfx_path is None
    assert args.certificate_password is None
    assert args.certificate_sha1 is None
    assert args.certificate_subject is None
    assert args.certificate_auto_select is False
    assert args.code_sign is False


def test_get_arguments_signing_flags(monkeypatch):
    """Signing CLI flags should be parsed correctly."""
    monkeypatch.setattr(
        "sys.argv",
        [
            "pyship",
            "--pfx-path",
            "cert.pfx",
            "--certificate-password",
            "secret",
            "--certificate-sha1",
            "aabb" * 10,
            "--certificate-subject",
            "My Co",
            "--certificate-auto-select",
            "--code-sign",
        ],
    )
    args = get_arguments()
    assert args.pfx_path == "cert.pfx"
    assert args.certificate_password == "secret"
    assert args.certificate_sha1 == "aabb" * 10
    assert args.certificate_subject == "My Co"
    assert args.certificate_auto_select is True
    assert args.code_sign is True


def test_get_arguments_cloud_flags(monkeypatch):
    """Cloud CLI flags should be parsed correctly."""
    monkeypatch.setattr(
        "sys.argv",
        [
            "pyship",
            "--profile",
            "myprofile",
            "--id",
            "AKID",
            "--secret",
            "shhh",
            "--noupload",
            "--public-readable",
        ],
    )
    args = get_arguments()
    assert args.profile == "myprofile"
    assert args.id == "AKID"
    assert args.secret == "shhh"
    assert args.noupload is True
    assert args.public_readable is True
