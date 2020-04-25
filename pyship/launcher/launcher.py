import os
import sys
import subprocess
from pathlib import Path
from semver import parse_version_info

from balsa import Balsa, get_logger
from ismain import is_main

from pyship import restart_value, __application_name__, __author__

# Just for the launcher, not the user's app that pyship is launching
launcher_application_name = f"{__application_name__}_launcher"

log = get_logger(launcher_application_name)


def setup_logging(target_app_name: str):
    balsa = Balsa(launcher_application_name, __author__, gui=True)
    if len(sys.argv) > 1 and (sys.argv[1].lower().startswith("-v") or sys.argv[1].lower().startswith("--v")):
        balsa.verbose = True

    # use Sentry's exception service
    sentry_dsn = os.environ.get(f"SENTRY_DSN_{target_app_name.upper()}")
    if sentry_dsn is not None:
        balsa.sentry_dsn = sentry_dsn
        balsa.use_sentry = True

    balsa.init_logger()


def launch() -> int:
    """
    launch the pyship app
    :return: 0 if no error, non-zero on error (like Windows apps)
    """

    target_app_name = os.path.basename(sys.argv[0]).replace(".exe", "")

    setup_logging(target_app_name)

    log.info(f"{target_app_name}")

    # 1) find the latest <application_name>_<version>
    # 2) execute it via python -m <application_name>
    # 3) inside the program, it has option to call pyship module's upgrade() function.  If an upgrade happens, upgrade() will return True
    #    and the program has the option to call pyship's request_restart() and then exit (it will automatically get restarted).
    # 4) look in Program Data for a restart request (that was set via upgrade() ) - if so, do this all over again

    # the pyship program executes out of data space
    # program_dir = os.path.join(appdirs.user_data_dir(target_app_name, launcher_author))

    # get latest version
    cwd = Path().resolve()
    glob_string = f"{target_app_name}_*"
    glob_list = cwd.glob(glob_string)
    log.info(f"{glob_list}")
    latest_version = None
    versions = []
    for candidate_dir in glob_list:
        if candidate_dir.is_dir():
            candidate_string_fields = str(candidate_dir).split("_")
            if len(candidate_string_fields) > 0:
                version = candidate_string_fields[-1]
                try:
                    semver = parse_version_info(version)
                except ValueError:
                    semver = None
                if semver is not None:
                    versions.append(semver)
            else:
                log.error(f"could not get version out of {candidate_dir}")

    if len(versions) > 0:
        versions.sort()
        latest_version = str(versions[-1])
        log.info(f"latest_version={latest_version}")
    else:
        log.error(f"could not find any expected application version in {cwd}")

    ok_return_code = 0
    error_return_code = 1

    if latest_version is None:
        return_code = error_return_code
    else:
        # see:
        # http://www.trytoprogram.com/batch-file-return-code/
        return_code = None
        while return_code is None or return_code == restart_value:

            # locate the python interpreter executable
            python_exe_path = None
            python_exe_parent_dir = os.path.join(f"{target_app_name}_{latest_version}")
            # the installer would have left exactly one of these python executables
            for python_exe_candidate in ["python.exe", "pythonw.exe"]:
                python_exe_candidate_path = os.path.join(python_exe_parent_dir, python_exe_candidate)
                if os.path.exists(python_exe_candidate_path):
                    python_exe_path = python_exe_candidate_path

            if python_exe_path is None:
                log.error(f"python exe not found at {python_exe_parent_dir}")
                return_code = 2	 # Indicates that the system cannot find the file in that specified location
            else:
                # run the target app using the python interpreter we just found
                cmd = [python_exe_path, "-m", target_app_name]
                log.info(f"{cmd}")
                try:
                    target_process = subprocess.run(cmd, capture_output=True, text=True)
                    if target_process.returncode != ok_return_code and target_process.returncode != restart_value:
                        for out in [target_process.stdout, target_process.stderr]:
                            if out is not None:
                                stripped_out = out.strip()
                                if len(stripped_out) > 0:
                                    log.error(out.strip())

                    return_code = target_process.returncode  # if app returns "restart_value" then it wants to be restarted
                except FileNotFoundError as e:
                    log.error(f"{e} {cmd}")
                    return_code = error_return_code

    return return_code


if is_main():
    sys.exit(launch())
