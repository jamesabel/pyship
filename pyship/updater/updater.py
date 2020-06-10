from abc import ABC, abstractmethod
import typing
from pathlib import Path
from enum import Enum
from dataclasses import dataclass

from semver import VersionInfo

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
    def get_pyshipy(self, pyshipy_source, destination_dir: Path):
        """
        get a pyshipy dir from the pyshipy_source
        :param pyshipy_source: place to get the pyshipy dir (type is dependent on the derived class)
        :param destination_dir: dir to put the pyshipy dir
        """
        ...

    def get_greatest_version(self, available_versions: dict) -> (VersionInfo, None):
        log.debug(f"{available_versions=}")
        if len(available_versions) == 0:
            greatest_version = None
        else:
            greatest_version = sorted(list(available_versions.keys()))[-1]
        log.info(f"{greatest_version=}")
        return greatest_version

    def update(self, current_version: (str, VersionInfo)):
        """
        update this (the target) application (pyshipy dir)
        """
        if isinstance(current_version, str):
            current_version = VersionInfo.parse(current_version)
        available_versions = self.get_available_versions()
        greatest_version = self.get_greatest_version(available_versions)
        log.info(f"{greatest_version=}")
        log.info(f"{available_versions[greatest_version]=}")
        if greatest_version is not None and greatest_version > current_version:
            self.get_pyshipy(available_versions[greatest_version], Path(".."))

