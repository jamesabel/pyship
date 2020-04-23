from typeguard import typechecked
from typing import Callable

from sundry import local_time_string
from balsa import Balsa
from balsa import get_logger as balsa_get_logger

from pyship import __application_name__


class PyshipLog(Balsa):
    pass


@typechecked(always=True)
def get_logger(name: str):
    return balsa_get_logger(name)


log = get_logger(__application_name__)


@typechecked(always=True)
def log_process_output(output_type: str, process_output: bytes, log_function: Callable = log.debug) -> list:
    """
    log the output from a process call
    :param output_type: e.g. stderr, stdout
    :param process_output: actual characters from the process output (e.g. stdout or stderr)
    :param log_function: log function to call
    :return a list of the output lines
    """
    # log the output from a process call
    lines = []
    for line in process_output.decode("utf-8").splitlines():
        line = line.strip()
        if len(line) > 0:
            lines.append(line)
    for line in lines:
        log_function(f"{output_type} : {line.strip()}")
    return lines


def pyship_print(s: str):
    log.info(s)
    print(f"{local_time_string()} : {s}")
