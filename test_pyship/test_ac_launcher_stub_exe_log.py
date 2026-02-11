import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from ismain import is_main

from pyship.launcher_stub import compile_launcher_stub

APP_NAME = "tstlogstub"


def test_launcher_stub_exe_writes_log():
    """Compile the C# launcher stub, run it (no CLIPs exist), and verify the log file is written correctly."""

    local_app_data = Path(os.environ["LOCALAPPDATA"])
    log_dir = local_app_data / APP_NAME / "log"
    log_file = log_dir / f"{APP_NAME}_launcher.log"

    # Clean up any leftover log directory from a previous run
    app_data_dir = local_app_data / APP_NAME
    if app_data_dir.exists():
        shutil.rmtree(app_data_dir, ignore_errors=True)

    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # The stub derives paths from its own exe location:
            #   launcherDir = directory containing the exe
            #   appDir = parent of launcherDir
            # So we create: tmp/tstlogstub/tstlogstub.exe
            launcher_dir = tmp_path / APP_NAME
            exe_path = compile_launcher_stub(APP_NAME, icon_path=None, is_gui=False, output_path=launcher_dir)

            assert exe_path.exists(), f"compiled exe not found at {exe_path}"

            # Run the stub — it will find no CLIP directories and exit with code 1
            result = subprocess.run([str(exe_path)], capture_output=True, timeout=10)
            assert result.returncode == 1, f"expected exit code 1, got {result.returncode}"

            # Verify the log file was created and has content
            assert log_file.exists(), f"log file not found at {log_file}"
            log_content = log_file.read_text(encoding="utf-8")
            assert len(log_content) > 0, "log file is empty"

            lines = log_content.strip().splitlines()

            # Verify log line format: "timestamp - tstlogstub_stub - LEVEL - message"
            log_line_pattern = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - " + APP_NAME + r"_stub - (INFO|ERROR) - ")
            for line in lines:
                assert log_line_pattern.match(line), f"log line does not match expected format: {line}"

            # Verify key log messages are present
            assert any("stub starting" in line for line in lines), "missing 'stub starting' log line"
            assert any("no command-line arguments" in line for line in lines), "missing 'no command-line arguments' log line"
            assert any(f"appName={APP_NAME}" in line for line in lines), "missing 'appName=' log line"
            assert any("searching for CLIP directories" in line for line in lines), "missing 'searching for CLIP directories' log line"
            assert any("candidate directories found:" in line for line in lines), "missing 'candidate directories found' log line"
            assert any("valid CLIPs" in line for line in lines), "missing 'valid CLIPs' log line"
            assert any("No Python environment found" in line for line in lines), "missing 'No Python environment found' error log line"

            # Verify at least one ERROR level line exists
            assert any("- ERROR -" in line for line in lines), "missing ERROR level log line"

    finally:
        # Clean up the log directory from %LOCALAPPDATA%
        if app_data_dir.exists():
            shutil.rmtree(app_data_dir, ignore_errors=True)


if is_main():
    test_launcher_stub_exe_writes_log()
