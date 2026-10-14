"""
Tests for issue #57: uv writes its normal status output to stderr, so a successful ``uv pip install``
must not produce warnings in the pyship log.

All tests and fixtures in this file are AI-authored (Claude Code); module-level constants are covered by this note.
"""

import logging
import subprocess
from pathlib import Path
from unittest.mock import patch

from pyship.uv_util import uv_pip_install

UV_STATUS_STDERR = "Using Python 3.14.3 environment at: app\\bup\\bup_0.14.4\nResolved 12 packages in 85ms\nInstalled 12 packages in 1.2s\n"


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_uv_pip_install_success_logs_stderr_at_info_only(tmp_path, caplog):
    completed = subprocess.CompletedProcess(args=["uv"], returncode=0, stdout="", stderr=UV_STATUS_STDERR)
    with caplog.at_level(logging.INFO, logger="pyship"), patch("pyship.uv_util.subprocess.run", return_value=completed):
        uv_pip_install(tmp_path / "uv.exe", tmp_path / "python.exe", ["ismain"], tmp_path / "dist", upgrade=True, system=True)

    assert not [record for record in caplog.records if record.levelno > logging.INFO]
    assert any("Resolved 12 packages" in record.getMessage() and record.levelno == logging.INFO for record in caplog.records)


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_uv_pip_install_success_with_empty_stderr_logs_nothing_above_info(tmp_path, caplog):
    completed = subprocess.CompletedProcess(args=["uv"], returncode=0, stdout="", stderr="")
    with caplog.at_level(logging.INFO, logger="pyship"), patch("pyship.uv_util.subprocess.run", return_value=completed):
        uv_pip_install(tmp_path / "uv.exe", tmp_path / "python.exe", ["ismain"], tmp_path / "dist")

    assert not [record for record in caplog.records if record.levelno > logging.INFO]


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_uv_pip_install_passes_find_links_only_when_dist_dir_exists(tmp_path):
    completed = subprocess.CompletedProcess(args=["uv"], returncode=0, stdout="", stderr="")
    dist_dir = tmp_path / "dist"
    with patch("pyship.uv_util.subprocess.run", return_value=completed) as mock_run:
        uv_pip_install(tmp_path / "uv.exe", tmp_path / "python.exe", ["ismain"], dist_dir)
        assert "-f" not in mock_run.call_args[0][0]
        dist_dir.mkdir()
        uv_pip_install(tmp_path / "uv.exe", tmp_path / "python.exe", ["ismain"], dist_dir)
        cmd = mock_run.call_args[0][0]
        assert cmd[cmd.index("-f") + 1] == str(Path(dist_dir))
