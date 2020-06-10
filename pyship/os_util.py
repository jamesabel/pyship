import os
import shutil
import time
from pathlib import Path
import stat
from platform import system
from platform import architecture

from typeguard import typechecked

from pyship import get_logger, __application_name__, pyship_print

log = get_logger(__application_name__)


@typechecked(always=True)
def is_windows() -> bool:
    return system() == "Windows"


@typechecked(always=True)
def get_target_os() -> (str, None):
    if is_windows():
        bit_string, os_string = architecture()
        target_os = f"{os_string[0:3].lower()}{bit_string[0:2]}"
    else:
        target_os = None
    return target_os


@typechecked(always=True)
def remove_readonly(path: Path):
    os.chmod(str(path), stat.S_IWRITE)


# sometimes needed for Windows
def _remove_readonly_onerror(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)


@typechecked(always=True)
def rmdir(p: Path, log_function=log.error) -> (bool, bool):
    retry_count = 0
    retry_limit = 4
    delete_ok = False
    delay = 1.0
    while p.exists() and retry_count < retry_limit:
        try:
            shutil.rmtree(p, onerror=_remove_readonly_onerror)
            delete_ok = True
        except FileNotFoundError as e:
            log.debug(str(e))  # this can happen when first doing the shutil.rmtree()
            time.sleep(delay)
        except PermissionError as e:
            log.info(str(e))
            time.sleep(delay)
        except OSError as e:
            log.info(str(e))
            time.sleep(delay)
        time.sleep(0.1)
        if p.exists:
            time.sleep(delay)
        retry_count += 1
        delay *= 2.0
    if p.exists():
        log_function(f'could not remove {p} ({retry_count=})', stack_info=True)
    else:
        delete_ok = True
    return delete_ok


@typechecked(always=True)
def mkdirs(d: Path, remove_first: bool = False, log_function=log.error):
    """
    make directories recursively, optionally deleting first
    :param d: directory to make
    :param remove_first: True to delete directory contents first
    :param log_function: log function
    """
    if remove_first:
        rmdir(d, log_function)
    # sometimes when os.makedirs exits the dir is not actually there
    count = 600
    while count > 0 and not d.exists():
        try:
            # for some reason we can get the FileNotFoundError exception
            d.mkdir(parents=True, exist_ok=True)
        except FileNotFoundError:
            pass
        if not d.exists():
            time.sleep(0.1)
        count -= 1
    if not d.exists():
        log_function(f'could not mkdirs "{d}" ({d.absolute()})')


@typechecked(always=True)
def copy_tree(source: Path, dest: Path, subdir: str):
    # copy the tree, but don't copy things like __pycache__
    dest.mkdir(parents=True, exist_ok=True)
    source = Path(source, subdir)
    dest = Path(dest, subdir)
    log.info(f'copying "{source}" ("{source.resolve().absolute()}") to "{dest}" ("{dest.resolve().absolute()}")')
    shutil.copytree(str(source), str(dest), ignore=shutil.ignore_patterns("__pycache__"), dirs_exist_ok=True)
