import os
import shutil
import tarfile
import zipfile
from pathlib import Path

from typeguard import typechecked
import requests
from balsa import get_logger

from pyshipupdate import mkdirs
from pyship import __application_name__ as pyship_application_name

log = get_logger(pyship_application_name)


@typechecked
def file_download(url: str, destination_folder: Path, file_name: Path):
    destination_folder.mkdir(parents=True, exist_ok=True)
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
            raise Exception(f"error getting {file_name} from {url}")
    return destination_path


def is_within_directory(directory: Path, target: Path):
    abs_directory = directory.absolute()
    abs_target = target.absolute()
    prefix = os.path.commonprefix([abs_directory, abs_target])
    return prefix == str(abs_directory)


def safe_extract(tar, path: Path = Path(".")):
    for member in tar.getmembers():
        member_path = Path(path, member.name)
        if not is_within_directory(path, member_path):
            raise Exception("Attempted Path Traversal in Tar File")
    tar.extractall(path, None, numeric_owner=False)


@typechecked
def extract(source_folder: Path, source_file: Path, destination_folder: Path):
    mkdirs(destination_folder, remove_first=True)
    source = Path(source_folder, source_file)
    log.debug(f"extracting {source} to {destination_folder}")
    if source_file.suffix == ".zip":
        with zipfile.ZipFile(source) as zf:
            # assumes a trusted .zip
            zf.extractall(destination_folder)
    elif source_file.suffix == ".tgz":
        with tarfile.open(source) as tf:
            safe_extract(tf, destination_folder)
    elif source_file.suffix == ".gz":
        with tarfile.open(source) as tf:
            safe_extract(tf, destination_folder)
    else:
        raise Exception(f"Unsupported file type {source_file.suffix} ({source_file})")
