"""
Standalone launcher script for pyship applications.

This script is designed to be self-contained (stdlib only, no third-party imports)
so it can be run by any Python interpreter without additional dependencies.

It is invoked by the C# launcher stub:
    python.exe {app_name}_launcher.py --app-dir <app_dir> [app args...]
"""

import sys
import os
import re
import json
import time
import logging
import subprocess
import argparse
from pathlib import Path

# Return codes (matching pyshipupdate constants)
OK_RETURN_CODE = 0
ERROR_RETURN_CODE = 1
CAN_NOT_FIND_FILE_RETURN_CODE = 2
RESTART_RETURN_CODE = 13

# Python interpreter executables by GUI mode
PYTHON_INTERPRETER_EXES = {True: "pythonw.exe", False: "python.exe"}


class RestartMonitor:
    """
    Monitor application restarts and detect excessive restart frequency.
    """

    def __init__(self):
        self.restarts = []
        self.max_samples = 4
        self.quick = 60.0  # this time or less (in seconds) is considered a quick restart

    def add(self):
        self.restarts.append(time.time())
        if len(self.restarts) > self.max_samples:
            self.restarts.pop(0)

    def excessive(self):
        """
        Determine if there has been excessive frequency of restarts.
        :return: True if restarts have been excessive
        """
        if len(self.restarts) < self.max_samples:
            return False
        return all(j - i <= self.quick for i, j in zip(self.restarts[:-1], self.restarts[1:]))


def _compare_versions(version_str):
    """
    Convert a version string like "1.2.3" to a tuple of ints for comparison.
    :param version_str: version string
    :return: tuple of ints
    """
    parts = []
    for part in version_str.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def _setup_logging(app_name, is_gui):
    """
    Set up stdlib logging for the launcher.
    :param app_name: application name for the log
    :param is_gui: True for GUI app
    """
    log_dir = None
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        log_dir = Path(local_app_data, app_name, "log")
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            log_dir = None

    logger = logging.getLogger(f"{app_name}_launcher")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    if log_dir is not None:
        try:
            fh = logging.FileHandler(str(Path(log_dir, f"{app_name}_launcher.log")))
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except OSError:
            pass

    if not is_gui:
        ch = logging.StreamHandler()
        ch.setLevel(logging.ERROR)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger


def _init_sentry():
    """
    Optionally initialize Sentry if sentry_sdk is available.
    """
    try:
        import urllib.request
        import sentry_sdk

        try:
            response = urllib.request.urlopen("https://api.pyship.org/resources/pyship/sentry", timeout=5)
            if response.status == 200:
                data = json.loads(response.read().decode())
                sentry_dsn = data.get("dsn")
                if sentry_dsn:
                    sentry_sdk.init(sentry_dsn, default_integrations=False)
        except Exception:
            pass
    except ImportError:
        pass


def launch(app_dir=None, additional_path=None):
    """
    Launch the pyship application.
    :param app_dir: override app dir (mainly for testing)
    :param additional_path: additional search path for app (mainly for testing)
    :return: exit code (0 if no error)
    """
    return_code = None

    clip_regex = re.compile(r"([_a-z0-9]*)_([.0-9]+)", flags=re.IGNORECASE)

    # Default values in case metadata file is not found
    is_gui = False
    report_exceptions = True
    target_app_name = None
    target_app_author = "unknown"

    if app_dir is not None:
        app_dir = Path(app_dir).resolve()

    # Read metadata
    if app_dir is not None:
        for metadata_file_path in app_dir.glob("*_metadata.json"):
            try:
                with metadata_file_path.open() as metadata_file:
                    metadata = json.load(metadata_file)
                    target_app_name = metadata.get("app")
                    target_app_author = metadata.get("author", target_app_author)
                    is_gui = metadata.get("is_gui", is_gui)
                    report_exceptions = metadata.get("report_exceptions", report_exceptions)
            except (json.JSONDecodeError, OSError):
                pass

    if target_app_name is None:
        # Try to derive app name from CLIP directories
        if app_dir is not None:
            for d in app_dir.iterdir():
                if d.is_dir():
                    m = clip_regex.match(d.name)
                    if m and Path(d, "Scripts", "python.exe").exists():
                        target_app_name = m.group(1)
                        break

    log = _setup_logging(target_app_name or "pyship", is_gui)

    if report_exceptions:
        _init_sentry()

    log.info(f"app_dir={app_dir}")

    if target_app_name is None:
        log.error(f"could not derive target app name in {app_dir}")
        return ERROR_RETURN_CODE

    log.info(f"target_app_name={target_app_name}")

    glob_string = f"{target_app_name}_*"

    restart_monitor = RestartMonitor()

    while (return_code is None or return_code == RESTART_RETURN_CODE) and not restart_monitor.excessive():
        restart_monitor.add()

        search_dirs = []
        if app_dir is not None:
            search_dirs.append(app_dir)

        # Also search user data dir (matches platformdirs.user_data_dir layout)
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            user_data_dir = Path(local_app_data, target_app_author, target_app_name)
            if user_data_dir.exists():
                search_dirs.append(user_data_dir)

        if additional_path is not None:
            search_dirs.append(Path(additional_path))

        candidate_dirs = []
        for search_dir in search_dirs:
            for d in Path(search_dir).glob(glob_string):
                if d.is_dir():
                    candidate_dirs.append(d)

        versions = {}
        for candidate_dir in candidate_dirs:
            matches = clip_regex.match(candidate_dir.name)
            if matches is not None:
                version_str = matches.group(2)
                version_tuple = _compare_versions(version_str)
                if any(v > 0 for v in version_tuple):
                    versions[version_tuple] = candidate_dir
                else:
                    log.error(f"could not get version out of {candidate_dir}")

        if len(versions) > 0:
            latest_version = sorted(versions.keys())[-1]
            log.info(f"latest_version={'.'.join(str(v) for v in latest_version)}")

            python_exe_path = Path(versions[latest_version], "Scripts", PYTHON_INTERPRETER_EXES[is_gui])

            if python_exe_path.exists():
                cmd = [str(python_exe_path), "-m", target_app_name]
                # Forward any extra arguments (skip --app-dir and its value)
                forwarded_args = _get_forwarded_args()
                cmd.extend(forwarded_args)

                log.info(f"cmd={cmd}")
                try:
                    target_process = subprocess.run(cmd, cwd=str(python_exe_path.parent), capture_output=True, text=True)
                    return_code = target_process.returncode

                    std_out = target_process.stdout
                    std_err = target_process.stderr

                    # When pythonw.exe fails silently (no stderr), re-run with python.exe to capture the actual error
                    if is_gui and return_code not in (OK_RETURN_CODE, RESTART_RETURN_CODE) and not (std_err and std_err.strip()):
                        log.warning(f"pythonw.exe exited with return_code={return_code} but produced no error output, re-running with python.exe for diagnostics")
                        diag_python = Path(versions[latest_version], "Scripts", "python.exe")
                        if diag_python.exists():
                            diag_cmd = [str(diag_python), "-X", "faulthandler"] + cmd[1:]
                            log.info(f"diagnostic cmd={diag_cmd}")
                            try:
                                diag_process = subprocess.run(diag_cmd, cwd=str(python_exe_path.parent), capture_output=True, text=True)
                                std_out = diag_process.stdout
                                std_err = diag_process.stderr
                            except Exception as diag_e:
                                log.error(f"diagnostic re-run failed: {diag_e}")

                    if (std_err and std_err.strip()) or (return_code != OK_RETURN_CODE and return_code != RESTART_RETURN_CODE):
                        if std_out and std_out.strip():
                            log.warning(std_out)
                        if std_err and std_err.strip():
                            log.error(std_err)

                    for name, std_x, sys_f in [("stdout", std_out, sys.stdout), ("stderr", std_err, sys.stderr)]:
                        if std_x and std_x.strip():
                            for so_line in std_x.splitlines():
                                so_line_strip = so_line.strip()
                                if so_line_strip:
                                    log.info(f"{name}:{so_line_strip}")
                            print(std_x, file=sys_f)

                    log.info(f"return_code={return_code}")

                except FileNotFoundError as e:
                    log.error(f"{e} {cmd}")
                    return_code = ERROR_RETURN_CODE
            else:
                log.error(f"python exe not found at {python_exe_path}")
                return_code = CAN_NOT_FIND_FILE_RETURN_CODE
        else:
            log.error(f"could not find any expected application version in {search_dirs} ({glob_string=})")
            return_code = ERROR_RETURN_CODE
            break

    if restart_monitor.excessive():
        log.error(f"excessive restarts restarts={restart_monitor.restarts}")

    if return_code is None:
        return_code = ERROR_RETURN_CODE

    log.info(f"returning : return_code={return_code}")

    return return_code


def _get_forwarded_args():
    """
    Parse sys.argv to extract arguments that should be forwarded to the target app.
    Strips out --app-dir and its value.
    """
    args = []
    skip_next = False
    for i, arg in enumerate(sys.argv[1:], 1):
        if skip_next:
            skip_next = False
            continue
        if arg == "--app-dir":
            skip_next = True
            continue
        args.append(arg)
    return args


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="pyship standalone launcher")
    parser.add_argument("--app-dir", type=str, default=None, help="application directory")
    known_args, _ = parser.parse_known_args()

    exit_app_dir = None
    if known_args.app_dir:
        exit_app_dir = Path(known_args.app_dir)

    sys.exit(launch(app_dir=exit_app_dir))
