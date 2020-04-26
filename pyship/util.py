import os
import shutil
import time
import tarfile
import zipfile
from pathlib import Path

from typeguard import typechecked
import requests
from balsa import get_logger

from pyship import __application_name__ as pyship_application_name

log = get_logger(pyship_application_name)


@typechecked(always=True)
def rm_mk_tree(dir_path: Path) -> bool:
    """
    Clears out a dir.  Makes it if it doesn't exist.
    :param dir_path: dir to clear out
    :return: True on success
    """

    # fancy rmtree, since for some reason shutil.rmtree can return before the tree is actually removed
    count = 0
    log.debug("removing %s (%s)", dir_path, dir_path.absolute())
    while dir_path.exists() and count < 30:
        try:
            shutil.rmtree(dir_path)
        except FileNotFoundError:
            pass
        except IOError:
            if count > 1:
                log.info("retrying removal of %s - perhaps you need to run this as sudo?", dir_path)
            time.sleep(1)
        count += 1
    if dir_path.exists():
        raise Exception(str(f"error: could not remove {dir_path} - exiting"))

    log.info("making %s (%s)", dir_path, dir_path.absolute())
    os.makedirs(str(dir_path), exist_ok=True)

    return count > 0


@typechecked(always=True)
def get_file(url: str, destination_folder: Path, file_name: Path):
    destination_path = Path(destination_folder, file_name)
    if destination_path.exists():
        log.info("using existing copy of %s from %s" % (file_name, os.path.abspath(destination_path)))
    else:
        log.info("get %s to %s" % (url, destination_path))
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(destination_path, "wb") as out_file:
                shutil.copyfileobj(response.raw, out_file)
            del response
        else:
            raise Exception("error getting {} from {}".format(file_name, url))
    return destination_path


@typechecked(always=True)
def extract(source_folder: Path, source_file: Path, destination_folder: Path):
    rm_mk_tree(destination_folder)
    source = Path(source_folder, source_file)
    log.debug(f"extracting {source} to {destination_folder}")
    if source_file.suffix == ".zip":
        with zipfile.ZipFile(source) as zf:
            # assumes a trusted .zip
            zf.extractall(destination_folder)
    elif source_file.suffix == ".tgz":
        with tarfile.open(source) as tf:
            tf.extractall(destination_folder)
    elif source_file.suffix == ".gz":
        with tarfile.open(source) as tf:
            tf.extractall(destination_folder)
    else:
        raise Exception(f"Unsupported file type {source_file} (extension : {extension})")


@typechecked(always=True)
def get_folder_size(folder_path: Path) -> int:
    total_size = 0
    for d, _, fns in os.walk(str(folder_path)):
        for f in fns:
            total_size += os.path.getsize(os.path.join(d, f))
    return total_size


@typechecked(always=True)
def get_pyship_sub_dir(application_name: str) -> str:
    application_module = __import__(application_name)
    application_version = application_module.__version__
    return f"{pyship_application_name}_{application_name}_{application_version}"
