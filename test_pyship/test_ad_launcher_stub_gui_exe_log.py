import os
import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from ismain import is_main

from pyship.launcher_stub import compile_launcher_stub

APP_NAME = "tstloggui"


def _compile_fake_python_exe(output_path: Path) -> Path:
    """Compile a minimal C# exe that ignores all arguments and exits 0, named python.exe."""
    from pyship.launcher_stub import _find_csc_exe

    csc_exe = _find_csc_exe()
    assert csc_exe is not None, "csc.exe not found"

    cs_source = "class P { static int Main(string[] args) { return 0; } }\n"
    cs_file = output_path / "_fake_python.cs"
    cs_file.write_text(cs_source, encoding="utf-8")

    exe_path = output_path / "python.exe"
    result = subprocess.run(
        [str(csc_exe), "/target:exe", "/optimize+", "/nologo", f"/out:{exe_path}", str(cs_file)],
        capture_output=True,
        text=True,
    )
    cs_file.unlink(missing_ok=True)
    assert result.returncode == 0, f"fake python.exe compilation failed: {result.stderr}"
    return exe_path


def test_launcher_stub_gui_exe_writes_log():
    """Compile the GUI C# launcher stub, run it with a fake CLIP, and verify the log file has no errors.

    Creates a fake CLIP directory with a real python.exe and a minimal launcher script
    so the stub finds a valid environment and runs to completion without errors.
    """

    local_app_data = Path(os.environ["LOCALAPPDATA"])
    log_dir = local_app_data / APP_NAME / "log"
    log_file = log_dir / f"{APP_NAME}_launcher.log"
    print(f'log file path: "{log_file}"')

    # Clean up any leftover log directory from a previous run
    app_data_dir = local_app_data / APP_NAME
    if app_data_dir.exists():
        shutil.rmtree(app_data_dir, ignore_errors=True)

    proc = None
    with tempfile.TemporaryDirectory() as tmp:
        try:
            tmp_path = Path(tmp)

            # Directory layout the stub expects:
            #   appDir = tmp/
            #   launcherDir = tmp/tstloggui/       (contains the .exe and launcher script)
            #   clipDir     = tmp/tstloggui_0.0.1/ (contains Scripts/python.exe)
            launcher_dir = tmp_path / APP_NAME
            exe_path = compile_launcher_stub(APP_NAME, icon_path=None, is_gui=True, output_path=launcher_dir)
            assert exe_path.exists(), f"compiled exe not found at {exe_path}"

            # Create a fake CLIP directory with a minimal python.exe that exits 0
            clip_dir = tmp_path / f"{APP_NAME}_0.0.1"
            scripts_dir = clip_dir / "Scripts"
            scripts_dir.mkdir(parents=True)
            _compile_fake_python_exe(scripts_dir)

            # Create a minimal launcher script (the fake python.exe ignores it, but it must exist)
            launcher_script = launcher_dir / f"{APP_NAME}_launcher.py"
            launcher_script.write_text("", encoding="utf-8")

            # Start the stub — it should find the CLIP, run the fake python.exe, and exit with 0
            proc = subprocess.Popen([str(exe_path)])

            # Wait for the process to finish
            exit_code = proc.wait(timeout=15)
            proc = None  # process has exited, no need to kill in finally

            assert exit_code == 0, f"expected exit code 0, got {exit_code}"

            # Verify the log file was created and has content
            assert log_file.exists(), f"log file not found at {log_file}"
            log_content = log_file.read_text(encoding="utf-8")
            assert len(log_content) > 0, "log file is empty"

            lines = log_content.strip().splitlines()

            # Verify log line format: "timestamp - tstloggui_stub - LEVEL - message"
            log_line_pattern = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - " + APP_NAME + r"_stub - INFO - ")
            for line in lines:
                assert log_line_pattern.match(line), f"log line does not match expected format (unexpected ERROR?): {line}"

            # Verify key log messages are present
            assert any("stub starting" in line for line in lines), "missing 'stub starting' log line"
            assert any("no command-line arguments" in line for line in lines), "missing 'no command-line arguments' log line"
            assert any(f"appName={APP_NAME}" in line for line in lines), "missing 'appName=' log line"
            assert any("searching for CLIP directories" in line for line in lines), "missing 'searching for CLIP directories' log line"
            assert any("candidate directories found:" in line for line in lines), "missing 'candidate directories found' log line"
            assert any("valid CLIPs" in line for line in lines), "missing 'valid CLIPs' log line"
            assert any("selected latest CLIP" in line for line in lines), "missing 'selected latest CLIP' log line"
            assert any("pythonExe=" in line for line in lines), "missing 'pythonExe=' log line"
            assert any("starting process" in line for line in lines), "missing 'starting process' log line"
            assert any("process started - PID=" in line for line in lines), "missing 'process started' log line"
            assert any("process exited - exitCode=0" in line for line in lines), "missing 'process exited - exitCode=0' log line"

            # Verify NO error lines exist
            assert not any("- ERROR -" in line for line in lines), "unexpected ERROR log line found"

        finally:
            # Kill the GUI process if still running
            if proc is not None:
                proc.kill()
                proc.wait()

            # Clean up the log directory from %LOCALAPPDATA%
            if app_data_dir.exists():
                pass
                # shutil.rmtree(app_data_dir, ignore_errors=True)


if is_main():
    test_launcher_stub_gui_exe_writes_log()
