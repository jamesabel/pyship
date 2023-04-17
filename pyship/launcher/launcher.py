import sys
from pathlib import Path
from semver import VersionInfo
import json
import appdirs
import re
import logging
import subprocess
from typing import Union

from ismain import is_main
from balsa import HandlerType, get_logger
import requests
import sentry_sdk

from pyship import __application_name__, __author__
from pyship import __version__ as pyship_version
from pyship import PyshipLog, python_interpreter_exes
from pyshipupdate import restart_return_code, error_return_code, can_not_find_file_return_code, ok_return_code
from pyship.launcher import RestartMonitor

# Just for the launcher, not the user's app that pyship is launching
launcher_application_name = f"{__application_name__}_launcher"

log = get_logger(launcher_application_name)

launcher_verbose_string = "--launcher_verbose"


def setup_logging(is_gui: bool, report_exceptions: bool) -> bool:
    verbose = len(sys.argv) > 1 and sys.argv[1].lower() == launcher_verbose_string

    pyship_log = PyshipLog(launcher_application_name, __author__, gui=is_gui, verbose=verbose)

    if verbose:
        print(f"{pyship_log.log_path=}")

    exception_string = ""  # store exception strings here until logging gets set up

    if report_exceptions:
        # use Sentry's exception service
        sentry_dsn = None
        try:
            response = requests.get("https://api.pyship.org/resources/pyship/sentry")
            if response.status_code == 200:
                try:
                    sentry_dsn = json.loads(response.text)["dsn"]
                except json.decoder.JSONDecodeError as e:
                    exception_string = str(e)
        except KeyError as e:
            exception_string = str(e)
        except requests.exceptions.RequestException as e:
            exception_string = str(e)
        if sentry_dsn is not None:
            pyship_log.sentry_dsn = sentry_dsn

            # init sentry outside of balsa and turn off integrations to workaround bug:
            # ModuleNotFoundError: No module named 'sentry_sdk.integrations.excepthook'
            pyship_log.use_sentry = False
            sentry_sdk.init(sentry_dsn, default_integrations=False)

    pyship_log.init_logger()
    # UI log at a high level since the user will not see launcher output (unless something goes terribly wrong)
    for ht in [HandlerType.DialogBox, HandlerType.Console]:
        if ht in pyship_log.handlers:
            pyship_log.handlers[ht].setLevel(logging.ERROR)

    if len(exception_string) > 0:
        log.info(exception_string)  # don't present these to the user unless verbose selected

    log.info(f"{verbose=}")
    log.info(f"{pyship_version=}")

    return verbose


def launch(additional_path: Union[Path, None] = None, app_dir: Union[Path, None] = None) -> int:
    """
    launch the pyship app
    :param additional_path - additional search path for app (mainly for testing)
    :param app_dir - override app dir (mainly for testing)
    :return: 0 if no error, non-zero on error (like Windows apps)
    """

    return_code = None

    # derive the target app name based on the clip dir(s) that exist
    clip_regex_string = "([_a-z0-9]*)_([.0-9]+)"
    clip_regex = re.compile(clip_regex_string, flags=re.IGNORECASE)  # simple format that accepts common semver (but not all semver)

    if app_dir is None:
        app_dir = Path(sys.executable).parent.parent.resolve().absolute()  # up one dir from where the python interpreter is

    # these should be set below, but in case there's no metadata file set them to something to allow the logging to be set up
    is_gui = False
    report_exceptions = True
    target_app_name = __application_name__
    target_app_author = __author__

    for metadata_file_path in app_dir.glob("*_metadata.json"):
        with metadata_file_path.open() as metadata_file:
            metadata = json.load(metadata_file)
            target_app_name = metadata.get("app")
            target_app_author = metadata.get("author", target_app_author)
            is_gui = metadata.get("is_gui", is_gui)
            report_exceptions = metadata.get("report_exceptions", report_exceptions)

    setup_logging(is_gui, report_exceptions)

    log.info(f"{app_dir=}")

    if target_app_name is None:
        log.error(f'could not derive target app name in {app_dir}")')
    else:
        log.info(f"{target_app_name=}")

        # 1) find the latest <application_name>_<version>
        # 2) execute it via python -m <application_name>
        # 3) inside the program, it has option to call pyship module's upgrade() function.  If an upgrade happens, upgrade() will return True
        #    and the program has the option to request a restart by returning the restart_return_code exit code.

        glob_string = f"{target_app_name}_*"  # clip directories will be of this form

        restart_monitor = RestartMonitor()

        while (return_code is None or return_code == restart_return_code) and not restart_monitor.excessive():
            restart_monitor.add()

            # todo: put finding the most recent app version in a function - I'll pretty sure this is done other places.  Also, it allows a unit test to be written for it.
            # find the most recent app version

            search_dirs = [app_dir, Path(appdirs.user_data_dir(target_app_name, target_app_author))]
            if additional_path is not None:
                search_dirs.append(additional_path)

            candidate_dirs = []
            for search_dir in search_dirs:
                for d in search_dir.glob(glob_string):
                    if d.is_dir():
                        candidate_dirs.append(d)

            versions = {}
            for candidate_dir in candidate_dirs:
                matches = re.match(clip_regex, candidate_dir.name)
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

                # locate the python interpreter executable
                python_exe_path = Path(versions[latest_version], python_interpreter_exes[is_gui])

                # run the target app using the python interpreter we just found
                if python_exe_path.exists():
                    cmd = [str(python_exe_path), "-m", target_app_name]
                    if len(sys.argv) > 1:
                        for arg in sys.argv[1:]:
                            if arg != launcher_verbose_string:
                                cmd.append(arg)  # pass along any arguments to the target application
                    log.info(f"{cmd}")
                    try:
                        # todo: this should work with PyInstaller, but it doesn't and I don't know why:
                        # return_code, _, _ = subprocess_run(cmd, cwd=python_exe_path.parent, mute_output=is_gui)  # if app returns "restart_value" then it wants to be restarted

                        # todo: so do this instead:
                        target_process = subprocess.run(cmd, cwd=python_exe_path.parent, capture_output=True, text=True)
                        return_code = target_process.returncode  # if app returns "restart_value" then it wants to be restarted

                        # Treatment of the output from the subprocess run in launcher is similar - but not exactly - the same as is in pyship/pyship_subprocess.py, so keep them separate for now.
                        # Maybe eventually we'll have just one shared routine once enough tests are in place.
                        std_out = target_process.stdout
                        std_err = target_process.stderr

                        if (std_err is not None and len(std_err.strip()) > 0) or (target_process.returncode != ok_return_code and target_process.returncode != restart_return_code):
                            # if there's a problem, log it with what the caller provides
                            for out, log_function in [(std_out, log.warning), (std_err, log.error)]:
                                if out is not None and len(out.strip()) > 0:
                                    log_function(out)

                        # log, and possibly print, each line of output from the process
                        for name, std_x, sys_f in [("stdout", std_out, sys.stdout), ("stderr", std_err, sys.stderr)]:
                            if std_x is not None and len(std_x.strip()) > 0:
                                for so_line in std_x.splitlines():
                                    so_line_strip = so_line.strip()
                                    if len(so_line_strip) > 0:
                                        log.info(f"{name}:{so_line_strip}")  # when logging, start with the name of the output string (stdout, stderr)

                                # output stdout, stderr that came (directly) from the process
                                print(std_x, file=sys_f)

                        log.info(f"{return_code=}")

                    except FileNotFoundError as e:
                        log.error(f"{e} {cmd}")
                        return_code = error_return_code
                else:
                    log.error(f"python exe not found at {python_exe_path}")
                    return_code = can_not_find_file_return_code

            else:
                log.error(f"could not find any expected application version in {search_dirs} ({glob_string=}))")

        if restart_monitor.excessive():
            log.error(f"excessive restarts {restart_monitor.restarts=}")

    if return_code is None:
        return_code = error_return_code

    log.info(f"returning : {return_code=}")

    return return_code


if is_main():
    sys.exit(launch())
