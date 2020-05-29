from pathlib import Path

from typeguard import typechecked


@typechecked(always=True)
def atomic_unzip(zip_path: Path, destination_dir: Path) -> bool:
    """
    Unzip a zip file to a directory in a safe, atomic way.  This avoids the issue where if an unzip fails it can potentially leave a directory with partially unzipped contents.
    In other words, atomic_unzip is all or nothing.
    :param zip_path: path to zip file to unzip
    :param destination_dir: destination dir for unzipped contents
    :return: True on success, False on failure
    """
    pass
