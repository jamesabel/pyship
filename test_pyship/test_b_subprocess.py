import sys

import pytest

from pyship import subprocess_run
from pyshipupdate import error_return_code, ok_return_code


def test_subprocess_run_basic_return_code():
    rc, stdout, stderr = subprocess_run([sys.executable, "--version"])
    assert rc == ok_return_code


def test_subprocess_run_stdout_captured():
    rc, stdout, stderr = subprocess_run([sys.executable, "-c", "print('hello_pyship_test')"])
    assert rc == ok_return_code
    assert stdout is not None
    assert "hello_pyship_test" in stdout


def test_subprocess_run_nonzero_exit():
    rc, stdout, stderr = subprocess_run([sys.executable, "-c", "import sys; sys.exit(2)"])
    assert rc == 2


def test_subprocess_run_stderr_captured():
    rc, stdout, stderr = subprocess_run([sys.executable, "-c", "import sys; sys.stderr.write('err_output')"])
    assert rc == ok_return_code
    assert stderr is not None
    assert "err_output" in stderr


def test_subprocess_run_with_cwd(tmp_path):
    rc, stdout, stderr = subprocess_run([sys.executable, "-c", "import os; print(os.getcwd())"], cwd=tmp_path)
    assert rc == ok_return_code
    assert stdout is not None
    # The cwd path should appear in stdout (may differ in case on Windows)
    assert str(tmp_path).lower() in stdout.lower()


def test_subprocess_run_file_not_found():
    rc, stdout, stderr = subprocess_run(["this_binary_does_not_exist_xyz_abc_123"])
    assert rc == error_return_code


def test_subprocess_run_returns_tuple_of_three():
    result = subprocess_run([sys.executable, "-c", "pass"])
    assert len(result) == 3


def test_subprocess_run_no_cwd():
    # Without cwd (NullPath default) it still executes successfully
    rc, stdout, stderr = subprocess_run([sys.executable, "-c", "print('ok')"])
    assert rc == ok_return_code
    assert stdout is not None
    assert "ok" in stdout


def test_subprocess_run_custom_log_functions():
    stdout_lines = []
    stderr_lines = []
    rc, stdout, stderr = subprocess_run(
        [sys.executable, "-c", "import sys; print('out'); sys.stderr.write('err')"],
        stdout_log=stdout_lines.append,
        stderr_log=stderr_lines.append,
    )
    assert rc == ok_return_code
