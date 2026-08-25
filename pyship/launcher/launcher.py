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
import shutil
import threading
import urllib.request
import zipfile
from pathlib import Path

# Return codes (matching pyshipupdate constants)
OK_RETURN_CODE = 0
ERROR_RETURN_CODE = 1
CAN_NOT_FIND_FILE_RETURN_CODE = 2
RESTART_RETURN_CODE = 13

# Python interpreter executables by UI mode
PYTHON_INTERPRETER_EXES = {"gui": "pythonw.exe", "cli": "python.exe", "tui": "python.exe"}


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


def _setup_logging(app_name, ui):
    """
    Set up stdlib logging for the launcher.
    :param app_name: application name for the log
    :param ui: UI mode ("cli", "tui", or "gui")
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

    if ui != "gui":
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
    ui = "cli"
    report_exceptions = True
    target_app_name = None
    target_app_author = "unknown"
    update_url = None

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
                    ui = metadata.get("ui", ui)
                    update_url = metadata.get("update_url", update_url)
                    # Legacy metadata compatibility
                    if "ui" not in metadata and "is_gui" in metadata:
                        ui = "gui" if metadata["is_gui"] else "cli"
                    report_exceptions = metadata.get("report_exceptions", report_exceptions)
            except (json.JSONDecodeError, OSError):
                pass

    if target_app_name is None:
        # Try to derive app name from CLIP directories
        if app_dir is not None:
            for d in app_dir.iterdir():
                if d.is_dir():
                    m = clip_regex.match(d.name)
                    if m and Path(d, "python.exe").exists():
                        target_app_name = m.group(1)
                        break

    log = _setup_logging(target_app_name or "pyship", ui)

    if report_exceptions:
        _init_sentry()

    log.info(f"app_dir={app_dir}")

    if target_app_name is None:
        log.error(f"could not derive target app name in {app_dir}")
        return ERROR_RETURN_CODE

    log.info(f"target_app_name={target_app_name}")

    glob_string = f"{target_app_name}_*"

    restart_monitor = RestartMonitor()
    update_thread = None

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

            # Self-update: once per launcher run, look for a newer CLIP on the update feed and
            # stage it in the user data dir, where the next launch will find it. Runs alongside
            # the app so startup is never delayed; daemon so an exit never waits on a download
            # (a partial one is cleaned up next time).
            if update_url is not None and update_thread is None:
                user_data_dir = _user_data_dir(target_app_author, target_app_name)
                if user_data_dir is not None:
                    update_thread = threading.Thread(
                        target=_check_for_update,
                        args=(update_url, target_app_name, latest_version, user_data_dir, log),
                        name=f"{target_app_name}_update",
                        daemon=True,
                    )
                    update_thread.start()

            python_exe_path = Path(versions[latest_version], PYTHON_INTERPRETER_EXES[ui])

            if python_exe_path.exists():
                cmd = [str(python_exe_path), "-m", target_app_name]
                # Forward any extra arguments (skip --app-dir and its value)
                forwarded_args = _get_forwarded_args()
                cmd.extend(forwarded_args)

                log.info(f"cmd={cmd}")
                try:
                    if ui == "tui":
                        # TUI: direct console access, unbuffered, no capture, no text wrapping
                        import signal

                        tui_cmd = [cmd[0], "-u"] + cmd[1:]  # -u = unbuffered stdout/stderr
                        old_sigint = signal.signal(signal.SIGINT, signal.SIG_IGN)
                        try:
                            target_process = subprocess.Popen(tui_cmd, cwd=str(python_exe_path.parent))
                            return_code = target_process.wait()
                        finally:
                            signal.signal(signal.SIGINT, old_sigint)

                    elif ui == "gui":
                        # GUI: capture output for diagnostics, use pythonw.exe
                        target_process = subprocess.run(cmd, cwd=str(python_exe_path.parent), capture_output=True, text=True)
                        return_code = target_process.returncode

                        std_out = target_process.stdout
                        std_err = target_process.stderr

                        # When pythonw.exe fails silently (no stderr), re-run with python.exe to capture the actual error
                        if return_code not in (OK_RETURN_CODE, RESTART_RETURN_CODE) and not (std_err and std_err.strip()):
                            log.warning(f"pythonw.exe exited with return_code={return_code} but produced no error output, re-running with python.exe for diagnostics")
                            diag_python = Path(versions[latest_version], "python.exe")
                            if diag_python.exists():
                                diag_cmd = [str(diag_python), "-X", "faulthandler"] + cmd[1:]
                                log.info(f"diagnostic cmd={diag_cmd}")
                                try:
                                    diag_process = subprocess.run(diag_cmd, cwd=str(python_exe_path.parent), capture_output=True, text=True)
                                    diag_return_code = diag_process.returncode
                                    std_out = diag_process.stdout
                                    std_err = diag_process.stderr
                                    if std_err and std_err.strip():
                                        log.info(f"diagnostic stderr captured (return_code={diag_return_code})")
                                    elif std_out and std_out.strip():
                                        log.info(f"diagnostic stdout captured (return_code={diag_return_code})")
                                    else:
                                        log.warning(f"diagnostic re-run with python.exe also produced no output (return_code={diag_return_code})")
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

                    else:
                        # CLI: inherited handles, no capture
                        target_process = subprocess.run(cmd, cwd=str(python_exe_path.parent))
                        return_code = target_process.returncode

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


def _user_data_dir(target_app_author, target_app_name):
    """
    Per-user directory the launcher also searches for CLIPs (platformdirs.user_data_dir layout).
    :return: Path, or None if %LOCALAPPDATA% is not set
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None
    return Path(local_app_data, target_app_author, target_app_name)


def _fetch_available_versions(update_url, timeout):
    """
    Ask the update feed which versions exist.
    :return: list of (version_tuple, version_string), newest last
    """
    with urllib.request.urlopen(f"{update_url}/versions", timeout=timeout) as response:
        feed = json.loads(response.read().decode("utf-8"))
    available = []
    for version_str in feed.get("versions", []):
        version_tuple = _compare_versions(str(version_str))
        if any(v > 0 for v in version_tuple):
            available.append((version_tuple, str(version_str)))
    available.sort()
    return available


def _install_clip(update_url, target_app_name, version_str, destination_dir, log, timeout):
    """
    Download <app>_<version>.clip from the feed and unpack it into destination_dir/<app>_<version>.
    Atomic from the launcher's point of view: the CLIP is unpacked into a .tmp dir and renamed
    into place only when complete, so a half-finished update is never mistaken for a version.
    :return: True if the CLIP was installed
    """
    clip_name = f"{target_app_name}_{version_str}"
    clip_path = Path(destination_dir, f"{clip_name}.clip.part")
    extract_tmp = Path(destination_dir, f"{clip_name}.tmp")
    extract_path = Path(destination_dir, clip_name)
    destination_dir.mkdir(parents=True, exist_ok=True)
    shutil.rmtree(extract_tmp, ignore_errors=True)
    try:
        # The feed answers with a redirect to a short-lived signed URL; urllib follows it.
        with urllib.request.urlopen(f"{update_url}/{clip_name}.clip", timeout=timeout) as response, clip_path.open("wb") as clip_file:
            shutil.copyfileobj(response, clip_file, length=1024 * 1024)
        log.info(f"downloaded {clip_path} ({clip_path.stat().st_size} bytes)")
        with zipfile.ZipFile(clip_path, "r") as zip_ref:
            zip_ref.extractall(extract_tmp)
        os.replace(extract_tmp, extract_path)
        log.info(f"installed {extract_path}")
        return True
    except (OSError, ValueError, zipfile.BadZipFile) as e:
        log.warning(f"update to {version_str} failed: {e}")
        shutil.rmtree(extract_tmp, ignore_errors=True)
        return False
    finally:
        try:
            clip_path.unlink()
        except OSError:
            pass


def _check_for_update(update_url, target_app_name, installed_version, user_data_dir, log, timeout=30.0):
    """
    If the update feed has a version newer than the newest installed one, stage it in
    user_data_dir for the next launch. Never raises: an update is a nicety, launching is not.
    :param update_url: base URL of the feed (metadata "update_url")
    :param installed_version: newest installed version, as a tuple of ints
    :return: True if a new version was installed
    """
    try:
        # Leftovers from an interrupted download/unpack on a previous run.
        for stale in list(user_data_dir.glob("*.clip.part")) + list(user_data_dir.glob("*.tmp")):
            if stale.is_dir():
                shutil.rmtree(stale, ignore_errors=True)
            else:
                stale.unlink(missing_ok=True)

        available = _fetch_available_versions(update_url, timeout)
        if not available:
            log.info(f"update feed {update_url} lists no versions")
            return False
        newest_tuple, newest_str = available[-1]
        installed_padded = installed_version + (0,) * (len(newest_tuple) - len(installed_version))
        newest_padded = newest_tuple + (0,) * (len(installed_version) - len(newest_tuple))
        if newest_padded <= installed_padded:
            log.info(f"up to date (installed={installed_version}, feed newest={newest_str})")
            return False
        if Path(user_data_dir, f"{target_app_name}_{newest_str}").exists():
            log.info(f"{newest_str} already staged")
            return False
        log.info(f"newer version available: {newest_str} (installed {installed_version}); downloading")
        return _install_clip(update_url, target_app_name, newest_str, user_data_dir, log, timeout)
    except (OSError, ValueError) as e:
        log.warning(f"update check against {update_url} failed: {e}")
        return False


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
