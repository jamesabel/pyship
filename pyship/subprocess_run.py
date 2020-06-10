import subprocess
from pathlib import Path
from typing import Callable

from typeguard import typechecked

from pyship import __application_name__, ok_return_code, restart_return_code, error_return_code, get_logger, pyship_print

log = get_logger(__application_name__)


@typechecked(always=True)
def subprocess_run(cmd: list, cwd: Path = None, capture_output: bool = True, stdout_log: Callable = log.info, stderr_log: Callable = log.warning) -> (int, (str, None), (str, None)):
    """
    subprocess run taking return code into account
    :param cmd: run command
    :param cwd: current directory
    :param capture_output: True to capture output
    :param stdout_log: function to call for stdout string
    :param stderr_log: function to call for stderr string
    :return: process return code, stdout, stderr
    """

    std_out = None
    std_err = None

    if cwd is not None:
        cwd = str(cwd)  # subprocess requires a string

    try:
        log.info(cmd)
        target_process = subprocess.run(cmd, cwd=cwd, capture_output=capture_output, text=True)
        if target_process.returncode != ok_return_code and target_process.returncode != restart_return_code:
            for out, log_function in [(target_process.stdout, stdout_log), (target_process.stderr, stderr_log)]:
                if out is not None and len(out.strip()) > 0:
                    log_function(out)
        std_out = target_process.stdout
        std_err = target_process.stderr

        return_code = target_process.returncode

    except FileNotFoundError as e:
        log.error(f"{e} {cmd}")
        return_code = error_return_code

    return return_code, std_out, std_err
