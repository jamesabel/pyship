from abc import ABC, abstractmethod
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

from semver import VersionInfo
from typeguard import typechecked

from pyship import get_logger, __application_name__, ModuleInfo

log = get_logger(__application_name__)


class PreReleaseTypes(Enum):
    test = "test"
    dev = "dev"
    alpha = "alpha"
    beta = "beta"


@dataclass
class Updater(ABC):
    """
    pyship updater
    Updates a pyship app to its latest released version.  Instantiated and called by a running pyship app.
    """

    target_app_name: str
    allowed_pre_release = []  # test, dev, beta, etc.

    @abstractmethod
    def get_available_versions(self) -> dict:
        """
        get available versions
        """
        ...

    @abstractmethod
    def install_pyshipy(self, version, destination_dir: Path) -> bool:
        """
        put a pyshipy into a destination dir
        :param version: version of pyshipy to get
        :param destination_dir: dir to put the pyshipy
        :return: True if were able to get the pyshipy, False otherwise
        """
        ...

    @typechecked(always=True)
    def get_greatest_version(self) -> (VersionInfo, None):
        """
        determine the greatest version and return it
        :return: the greatest version, or None if no versions available
        """
        available_versions = self.get_available_versions()
        log.debug(f"{available_versions=}")
        if len(available_versions) == 0:
            greatest_version = None
        else:
            greatest_version = sorted(list(available_versions.keys()))[-1]
        log.info(f"{greatest_version=}")
        return greatest_version

    @typechecked(always=True)
    def update(self, current_version: (str, VersionInfo), app_dir: Path = Path("..")) -> bool:
        """
        update this (the target) application (pyshipy dir)
        :param current_version: current version of the running app
        :param app_dir: application directory.  Normally this is just one level "up" from the execution directory, but this can be provided mainly for testing purposes.
        """
        did_update = False
        if isinstance(current_version, str):
            current_version = VersionInfo.parse(current_version)
        log.info(f"{current_version=}")
        greatest_version = self.get_greatest_version()
        log.info(f"{greatest_version=}")
        if greatest_version is not None:
            if greatest_version > current_version:
                did_update = self.install_pyshipy(greatest_version, app_dir)
        return did_update
