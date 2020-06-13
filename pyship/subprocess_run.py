import subprocess
from pathlib import Path
from typing import Callable
import sys
import os

from typeguard import typechecked

from pyship import __application_name__, ok_return_code, restart_return_code, error_return_code, get_logger, pyship_print

log = get_logger(__application_name__)


@typechecked(always=True)
def subprocess_run(cmd: list, cwd: Path = None, mute_output: bool = True, stdout_log: Callable = log.info, stderr_log: Callable = log.warning) -> (int, (str, None), (str, None)):
    """
    subprocess run taking return code into account
    :param cmd: run command
    :param cwd: current directory
    :param mute_output: True to mute output, False to sent output to stdout/stderr
    :param stdout_log: function to call for stdout string
    :param stderr_log: function to call for stderr string
    :return: process return code, stdout, stderr
    """

    std_out = None
    std_err = None

    if cwd is not None:
        cwd = str(cwd)  # subprocess requires a string

    try:
        log.info(f"{cmd=}")
        log.info(f"{cwd=}")
        log.info(f"{mute_output=}")
        log.info(f"{os.getcwd()=}")
        target_process = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        std_out = target_process.stdout
        std_err = target_process.stderr
        if (std_err is not None and len(std_err.strip()) > 0) or (target_process.returncode != ok_return_code and target_process.returncode != restart_return_code):
            # if there's a problem, output it with what the caller provides
            for out, log_function in [(std_out, stdout_log), (std_err, stderr_log)]:
                if out is not None and len(out.strip()) > 0:
                    log_function(out)
        log.debug(f"{std_out=}")
        log.debug(f"{std_err=}")
        if not mute_output:
            # output stdout, stderr that came from the process
            for s, f in [(std_out, sys.stdout), (std_err, sys.stderr)]:
                if s is not None and len(s.strip()) > 0:
                    print(s, file=f)

        return_code = target_process.returncode

    except FileNotFoundError as e:
        log.error(f"{e} {cmd}")
        return_code = error_return_code

    log.info(f"{return_code=}")

    return return_code, std_out, std_err
