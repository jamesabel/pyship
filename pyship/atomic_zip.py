from pathlib import Path
from tempfile import mkdtemp
import zipfile
import os

from typeguard import typechecked

from pyship import mkdirs, rmdir, get_logger, __application_name__

log = get_logger(__application_name__)


@typechecked(always=True)
def atomic_unzip(zip_file_path: Path, destination_dir: Path) -> bool:
    """
    Unzip a zip file to a directory in a safe, atomic way.  This avoids the issue where if an unzip fails in the middle it can potentially leave a directory with partially unzipped contents.
    In other words, atomic_unzip is all or nothing.
    :param zip_file_path: path to zip file to unzip
    :param destination_dir: destination dir for unzipped contents
    :return: True on success, False on failure
    """

    log.info(f'unzipping "{zip_file_path}" to "{destination_dir}"')
    success_flag = False
    temp_dir = mkdtemp(dir=destination_dir.parent)
    try:
        mkdirs(temp_dir, True)

        zip_ref = zipfile.ZipFile(zip_file_path, "r")
        zip_ref.extractall(temp_dir)
        zip_ref.close()

        rmdir(destination_dir)  # in case dest already exists
        os.rename(temp_dir, str(destination_dir))
        success_flag = True
    except IOError as e:
        log.info(f"{zip_file_path=} {destination_dir=} {e}")

    return success_flag
