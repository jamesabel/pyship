"""
Tests for issue #53: signtool's ``/p`` is the PFX password and requires ``/f``, so token mode must never
emit it even when ``certificate_password`` is set.

All tests and fixtures in this file are AI-authored (Claude Code); the module-level constants are covered by this note.
"""

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from pyship.signing import SigningConfig, sign_file, sign_file_token

VALID_SHA1 = "aa" * 20
TIMESTAMP_URL = "http://timestamp.example.com"


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
@pytest.fixture()
def signtool_exe(tmp_path: Path) -> Path:
    exe = tmp_path / "signtool.exe"
    exe.write_bytes(b"")
    return exe


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
@pytest.fixture()
def target_exe(tmp_path: Path) -> Path:
    exe = tmp_path / "target.exe"
    exe.write_bytes(b"MZ")
    return exe


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
@pytest.fixture()
def pfx_file(tmp_path: Path) -> Path:
    pfx = tmp_path / "cert.pfx"
    pfx.write_bytes(b"pfx")
    return pfx


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
@pytest.mark.parametrize(
    "selector",
    [
        {"certificate_sha1": VALID_SHA1},
        {"certificate_subject": "My Company"},
        {"certificate_auto_select": True},
    ],
)
def test_sign_file_token_never_passes_p_even_with_password(target_exe, signtool_exe, selector):
    config = SigningConfig(certificate_password="123456", signtool_path=signtool_exe, timestamp_url=TIMESTAMP_URL, **selector)
    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)) as mock_run:
        assert sign_file_token(target_exe, config) is True

    cmd = mock_run.call_args[0][0]
    assert "/p" not in cmd
    assert "/f" not in cmd
    assert "123456" not in cmd


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_sign_file_token_logs_that_password_is_ignored(target_exe, signtool_exe, caplog):
    config = SigningConfig(certificate_sha1=VALID_SHA1, certificate_password="123456", signtool_path=signtool_exe, timestamp_url=TIMESTAMP_URL)
    with caplog.at_level(logging.INFO, logger="pyship"), patch("pyship.signing.subprocess_run", return_value=(0, None, None)):
        sign_file_token(target_exe, config)

    assert any("ignored in token mode" in record.getMessage() for record in caplog.records)
    assert not any("123456" in record.getMessage() for record in caplog.records)


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_sign_file_token_without_password_does_not_log_ignore_note(target_exe, signtool_exe, caplog):
    config = SigningConfig(certificate_sha1=VALID_SHA1, signtool_path=signtool_exe, timestamp_url=TIMESTAMP_URL)
    with caplog.at_level(logging.INFO, logger="pyship"), patch("pyship.signing.subprocess_run", return_value=(0, None, None)):
        sign_file_token(target_exe, config)

    assert not any("ignored in token mode" in record.getMessage() for record in caplog.records)


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_sign_file_pfx_passes_p_with_f(target_exe, pfx_file, signtool_exe):
    config = SigningConfig(pfx_path=pfx_file, certificate_password="secret", signtool_path=signtool_exe, timestamp_url=TIMESTAMP_URL)
    with patch("pyship.signing.subprocess_run", return_value=(0, None, None)) as mock_run:
        assert sign_file(target_exe, config) is True

    cmd = mock_run.call_args[0][0]
    assert cmd[cmd.index("/f") + 1] == str(pfx_file)
    assert cmd[cmd.index("/p") + 1] == "secret"
