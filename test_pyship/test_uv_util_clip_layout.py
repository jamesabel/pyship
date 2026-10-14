"""
Regression tests for the CLIP interpreter layout and the subprocess environment used to build it.

Two independent faults made test_cloud fail whenever uv had to build a legacy (setup.py-only) dependency such as
mttkinter into a fresh CLIP:

- the ``python3XY._pth`` next to the DLL hijacks sys.path of every venv derived from the CLIP interpreter, so uv's
  isolated build environment could not see setuptools (and pyvenv.cfg alone makes Python 3.13 and older install into
  the parent directory). The runtime layout is therefore written by ``finalize_clip_python`` after the last install.
- a uv-created venv exports PYTHONHOME to child processes, so a CLIP interpreter of another version picked up the
  wrong standard library. ``python_subprocess_env`` strips those variables.

All tests, fixtures and helpers in this file are AI-authored (Claude Code).
"""

import os
import platform
import subprocess
import tarfile
from pathlib import Path

from pyship import SUPPORTED_PYTHON_VERSIONS
from pyship.subprocess import PYTHON_STEERING_ENV_VARS, python_subprocess_env, subprocess_run
from pyship.uv_util import copy_standalone_python, finalize_clip_python, find_or_bootstrap_uv, uv_pip_install

PROBE_NAME = "pyship_legacy_probe"
PROBE_VERSION = "0.0.1"


def _make_legacy_sdist(dist_dir: Path) -> Path:
    """Create a minimal setup.py-only sdist (no pyproject.toml, no PKG-INFO) so uv must run a build backend."""
    src_dir = dist_dir / f"{PROBE_NAME}-{PROBE_VERSION}"
    src_dir.mkdir(parents=True)
    (src_dir / "setup.py").write_text(f'from setuptools import setup\n\nsetup(name="{PROBE_NAME}", version="{PROBE_VERSION}", py_modules=["{PROBE_NAME}"])\n')
    (src_dir / f"{PROBE_NAME}.py").write_text('PROBE = "ok"\n')
    sdist_path = dist_dir / f"{PROBE_NAME}-{PROBE_VERSION}.tar.gz"
    with tarfile.open(sdist_path, "w:gz") as tar:
        tar.add(src_dir, arcname=src_dir.name)
    return sdist_path


def _clip_python_version() -> str:
    """A supported CLIP Python version that differs from the running interpreter when possible, to expose PYTHONHOME leaks."""
    running = ".".join(platform.python_version_tuple()[:2])
    others = [v for v in SUPPORTED_PYTHON_VERSIONS if v != running]
    return others[-1] if others else SUPPORTED_PYTHON_VERSIONS[-1]


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_python_subprocess_env_strips_steering_vars_and_keeps_path(monkeypatch):
    for env_var in PYTHON_STEERING_ENV_VARS:
        monkeypatch.setenv(env_var, "leaked")
    monkeypatch.setenv("PATH", "keep-me")

    env = python_subprocess_env()

    assert not any(env_var in env for env_var in PYTHON_STEERING_ENV_VARS)
    assert env["PATH"] == "keep-me"
    assert os.environ["PYTHONHOME"] == "leaked"  # the caller's environment is untouched


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_subprocess_run_strips_pythonhome(monkeypatch):
    monkeypatch.setenv("PYTHONHOME", str(Path("definitely") / "not" / "a" / "python"))
    # sys.executable's own launcher may re-export PYTHONHOME; the child reports what subprocess_run handed it
    rc, stdout, _stderr = subprocess_run([os.environ["COMSPEC"], "/c", "echo PYTHONHOME=%PYTHONHOME%"])

    assert rc == 0
    assert stdout is not None
    assert "PYTHONHOME=%PYTHONHOME%" in stdout  # unexpanded: the variable does not exist in the child


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_finalize_clip_python_writes_runtime_layout(tmp_path):
    (tmp_path / "python3.dll").write_bytes(b"")
    (tmp_path / "python314.dll").write_bytes(b"")

    finalize_clip_python(tmp_path)

    assert (tmp_path / "pyvenv.cfg").read_text().splitlines()[0] == f"home = {tmp_path.resolve()}"
    assert (tmp_path / "python314._pth").read_text().splitlines() == [".", "Lib", "Lib\\site-packages", "DLLs"]


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_finalize_clip_python_keeps_existing_files(tmp_path):
    (tmp_path / "python314.dll").write_bytes(b"")
    (tmp_path / "pyvenv.cfg").write_text("home = custom\n")
    (tmp_path / "python314._pth").write_text("custom\n")

    finalize_clip_python(tmp_path)

    assert (tmp_path / "pyvenv.cfg").read_text() == "home = custom\n"
    assert (tmp_path / "python314._pth").read_text() == "custom\n"


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_finalize_clip_python_falls_back_without_dll(tmp_path):
    finalize_clip_python(tmp_path)
    assert (tmp_path / "python._pth").exists()


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_copy_standalone_python_finalize_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONHOME", str(tmp_path / "bogus_home"))  # simulate the uv venv launcher leak
    uv_path = find_or_bootstrap_uv(tmp_path / "cache")
    version = _clip_python_version()

    copy_standalone_python(uv_path, version, tmp_path / "raw", finalize=False)
    assert not (tmp_path / "raw" / "pyvenv.cfg").exists()
    assert list((tmp_path / "raw").glob("python3*._pth")) == []

    copy_standalone_python(uv_path, version, tmp_path / "final")
    assert (tmp_path / "final" / "pyvenv.cfg").exists()
    assert len(list((tmp_path / "final").glob("python3*._pth"))) == 1


# AI-GENERATED TEST (Claude Code) - delete this line to make this test human-owned.
def test_legacy_sdist_builds_into_clip_then_finalize(tmp_path, monkeypatch):
    """
    The test_cloud scenario, made deterministic: UV_NO_CACHE forces the sdist build (a cached wheel would mask a
    regression) and a bogus PYTHONHOME simulates running from a uv-created venv.
    """
    monkeypatch.setenv("UV_NO_CACHE", "1")
    monkeypatch.setenv("PYTHONHOME", str(tmp_path / "bogus_home"))
    dist_dir = tmp_path / "dist"
    _make_legacy_sdist(dist_dir)
    uv_path = find_or_bootstrap_uv(tmp_path / "cache")
    clip_dir = tmp_path / "clip"
    clip_python = copy_standalone_python(uv_path, _clip_python_version(), clip_dir, finalize=False)

    uv_pip_install(uv_path, clip_python, [PROBE_NAME, "ismain"], dist_dir, upgrade=True, system=True)
    finalize_clip_python(clip_dir)

    assert (clip_dir / "Lib" / "site-packages" / f"{PROBE_NAME}.py").exists()  # installed into the CLIP, not next to it
    assert not (tmp_path / "Lib").exists()
    code = f"import sys, ismain, {PROBE_NAME}; print({PROBE_NAME}.PROBE, sys.prefix == {str(clip_dir)!r})"
    result = subprocess.run([str(clip_python), "-c", code], capture_output=True, text=True, timeout=60)  # inherits the bogus PYTHONHOME on purpose
    assert result.returncode == 0, result.stderr
    assert result.stdout.split() == ["ok", "True"]
    assert result.stderr.strip() == ""  # no RuntimeWarnings about sys.prefix
