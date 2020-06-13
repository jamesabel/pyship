import sys
from pathlib import Path
from semver import VersionInfo
import json
import appdirs
import re

from ismain import is_main
import requests

import sentry_sdk


from pyship import __application_name__, __author__
from pyship import __version__ as pyship_version
from pyship import restart_return_code, error_return_code, can_not_find_file_return_code, subprocess_run, python_interpreter_exes
from pyship import PyshipLog, get_logger

# Just for the launcher, not the user's app that pyship is launching
launcher_application_name = f"{__application_name__}_launcher"

log = get_logger(launcher_application_name)

launcher_verbose_string = "--launcher_verbose"

def setup_logging(is_gui: bool, report_exceptions: bool) -> bool:

    verbose = len(sys.argv) > 1 and sys.argv[1].lower() == launcher_verbose_string

    pyship_log = PyshipLog(launcher_application_name, __author__, gui=is_gui, verbose=verbose)

    exception_string = None  # store exception strings here until logging gets set up

    if report_exceptions:
        # use Sentry's exception service
        sentry_dsn = None
        try:
            response = requests.get("https://api.pyship.org/resources/pyship/sentry")
            if response.status_code == 200:
                try:
                    sentry_dsn = json.loads(response.text)["dsn"]
                except json.decoder.JSONDecodeError as e:
                    exception_string = e
        except KeyError as e:
            exception_string = e
        except requests.exceptions.RequestException as e:
            exception_string = e
        if sentry_dsn is not None:
            pyship_log.sentry_dsn = sentry_dsn

            # init sentry outside of balsa and turn off integrations to workaround bug:
            # ModuleNotFoundError: No module named 'sentry_sdk.integrations.excepthook'
            pyship_log.use_sentry = False
            sentry_sdk.init(sentry_dsn, default_integrations=False)

    pyship_log.init_logger()

    if exception_string is not None:
        log.info(exception_string)  # don't present these to the user unless verbose selected

    log.info(f"{verbose=}")
    log.info(f"{pyship_version=}")

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

    pyship_parent = Path(sys.executable).parent.parent.resolve().absolute()  # up one dir from where the python interpreter is

    # these should be set below, but in case there's no metadata file set them to something to allow the logging to be set up
    is_gui = False
    report_exceptions = True
    target_app_name = __application_name__
    target_app_author = __author__

    for metadata_file_path in pyship_parent.glob("*_metadata.json"):
        with metadata_file_path.open() as f:
            metadata = json.load(f)
            target_app_name = metadata.get("app")
            target_app_author = metadata.get("author", target_app_author)
            is_gui = metadata.get("is_gui", is_gui)
            report_exceptions = metadata.get("report_exceptions", report_exceptions)

    setup_logging(is_gui, report_exceptions)

    log.info(f"{pyship_parent=}")

    if target_app_name is None:
        log.error(f'could not derive target app name in {pyship_parent}")')
    else:

        log.info(f"{target_app_name=}")

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
        parent_glob_list = [p for p in pyship_parent.glob(glob_string)]
        log.info(f"{parent_glob_list=}")

        user_data_dir = Path(appdirs.user_data_dir(target_app_name, target_app_author))
        user_data_glob_list = [p for p in user_data_dir.glob(glob_string)]
        log.info(f"{user_data_glob_list=}")

        total_glob_list = parent_glob_list + user_data_glob_list

        latest_version = None
        versions = {}
        for candidate_dir in total_glob_list:
            if candidate_dir.is_dir():
                matches = re.match(pyshipy_regex, candidate_dir.name)
                if matches is not None:
                    version = matches.group(2)
                    try:
                        semver = VersionInfo.parse(version)
                    except ValueError:
                        semver = None
                    if semver is not None:
                        versions[semver] = candidate_dir
                    else:
                        log.error(f"could not get version out of {candidate_dir}")

        if len(versions) > 0:
            latest_version = sorted(versions.keys())[-1]
            log.info(f"{latest_version=}")
        else:
            log.error(f'could not find any expected application version in {total_glob_list} (looked in "{pyship_parent}" and "{user_data_dir}")')

        if latest_version is not None:

            while return_code is None or return_code == restart_return_code:

                if return_code == restart_return_code:
                    log.info("restarting ...")

                # locate the python interpreter executable
                python_exe_path = Path(pyship_parent, f"{target_app_name}_{latest_version}", python_interpreter_exes[is_gui])

                # run the target app using the python interpreter we just found
                if python_exe_path.exists():
                    cmd = [python_exe_path, "-m", target_app_name]
                    if len(sys.argv) > 1:
                        for arg in sys.argv[1:]:
                            if arg != launcher_verbose_string:
                                cmd.append(arg)  # pass along any arguments to the target application
                    log.info(f"{cmd}")
                    try:
                        return_code, _, _ = subprocess_run(cmd, cwd=python_exe_path.parent, mute_output=is_gui)  # if app returns "restart_value" then it wants to be restarted
                    except FileNotFoundError as e:
                        log.error(f"{e} {cmd}")
                        return_code = error_return_code
                else:
                    log.error(f"python exe not found at {python_exe_path}")
                    return_code = can_not_find_file_return_code

    if return_code is None:
        return_code = error_return_code

    return return_code


if is_main():
    sys.exit(launch())
