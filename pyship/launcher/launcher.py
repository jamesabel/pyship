import os
import sys
from pathlib import Path
from semver import parse_version_info
import re
import json
from pprint import pprint
from logging import getLogger
import appdirs


from ismain import is_main

from pyship import __application_name__, __author__, restart_return_code, error_return_code, can_not_find_file_return_code, subprocess_run, python_interpreter_exes
from pyship import PyshipLog, get_logger

# Just for the launcher, not the user's app that pyship is launching
launcher_application_name = f"{__application_name__}_launcher"

log = getLogger(launcher_application_name)


def setup_logging(target_app_name: str, is_gui: bool) -> bool:

    if not is_gui:
        print("sys.argv:")
        pprint(sys.argv)  # todo: remove this one everything is working OK

    verbose = len(sys.argv) > 1 and (sys.argv[1].lower() == "-v" or sys.argv[1].lower() == "--verbose")

    balsa = PyshipLog(launcher_application_name, __author__, gui=is_gui, verbose=verbose)

    # use Sentry's exception service
    sentry_dsn = os.environ.get(f"SENTRY_DSN_{target_app_name.upper()}")
    if sentry_dsn is not None:
        balsa.sentry_dsn = sentry_dsn
        balsa.use_sentry = True

    balsa.init_logger()

    return verbose


def launch() -> int:
    """
    launch the pyship app
    :return: 0 if no error, non-zero on error (like Windows apps)
    """

    return_code = None

    # derive the target app name based on the pyshipy dir(s) that exist


    pyshipy_regex_string = "([_a-z0-9]*)_([.0-9]+)"
    pyshipy_regex = re.compile(pyshipy_regex_string, flags=re.IGNORECASE)  # simple format that accepts common semver (but not all semver)

    pyship_parent = Path("..")

    # these should be set below, but in case there's no metadata file set them to something to allow the logging to be set up
    is_gui = False
    target_app_name = __application_name__
    target_app_author = __author__

    for metadata_file_path in pyship_parent.glob("*_metadata.json"):
        with metadata_file_path.open() as f:
            metadata = json.load(f)
            target_app_name = metadata.get("app")
            target_app_author = metadata.get("author")
            is_gui = metadata.get("is_gui")

    verbose = setup_logging(target_app_name, is_gui)

    if target_app_name is None:
        log.error(f'could not derive target app name in {pyship_parent.absolute()}")')
    else:

        log.info(f"{target_app_name}")

        # 1) find the latest <application_name>_<version>
        # 2) execute it via python -m <application_name>
        # 3) inside the program, it has option to call pyship module's upgrade() function.  If an upgrade happens, upgrade() will return True
        #    and the program has the option to call pyship's request_restart() and then exit (it will automatically get restarted).
        # 4) look in Program Data for a restart request (that was set via upgrade() ) - if so, do this all over again

        # the pyship program executes out of data space
        # program_dir = os.path.join(appdirs.user_data_dir(target_app_name, launcher_author))

        # get latest version of the app to be launched
        glob_string = f"{target_app_name}_*"

        # get app versions in the parent directory of the launcher
        parent_glob_list = [p for p in Path("..").glob(glob_string)]
        log.info(f"{parent_glob_list=}")

        user_data_glob_list = [p for p in Path(appdirs.user_data_dir(target_app_name, target_app_author)).glob(glob_string)]
        log.info(f"{user_data_glob_list=}")

        latest_version = None
        versions = []
        for candidate_dir in parent_glob_list + user_data_glob_list:
            if candidate_dir.is_dir():
                matches = re.match(pyshipy_regex, candidate_dir.name)
                if matches is not None:
                    version = matches.group(2)
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

        if latest_version is not None:

            while return_code is None or return_code == restart_return_code:

                # locate the python interpreter executable
                python_exe_path = None
                is_gui = None
                python_exe_parent_dir = os.path.join(f"{target_app_name}_{latest_version}")
                # the installer would have left exactly one of these python executables
                for is_gui_candidate, python_exe_candidate in python_interpreter_exes.items():
                    python_exe_candidate_path = os.path.join(python_exe_parent_dir, python_exe_candidate)
                    if os.path.exists(python_exe_candidate_path):
                        python_exe_path = python_exe_candidate_path
                        is_gui = is_gui_candidate

                if is_gui is False:
                    print(f"found {python_exe_path}")

                # run the target app using the python interpreter we just found
                if python_exe_path is None:
                    log.error(f"python exe not found at {python_exe_parent_dir}")
                    return_code = can_not_find_file_return_code
                else:
                    cmd = [python_exe_path, "-m", target_app_name]
                    if len(sys.argv) > 1:
                        cmd.extend(sys.argv[1:])  # pass along any arguments to the target application
                    log.info(f"{cmd}")
                    try:
                        if is_gui is False:
                            print("subprocess:")
                            print(cmd)
                        return_code = subprocess_run(cmd, is_gui=is_gui)  # if app returns "restart_value" then it wants to be restarted
                    except FileNotFoundError as e:
                        log.error(f"{e} {cmd}")
                        return_code = error_return_code

    if return_code is None:
        return_code = error_return_code

    return return_code


if is_main():
    sys.exit(launch())
