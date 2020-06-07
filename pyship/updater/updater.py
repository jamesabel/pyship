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
    packaged_app_dirs = set()  # directories to search for packaged app (i.e. "dist" distribution dirs)
    allowed_pre_release = []  # test, dev, beta, etc.
    available_versions = set()

    def get_available_versions(self) -> (typing.List[VersionInfo], None):
        """
        get available versions
        """
        [self.available_versions.add(ModuleInfo(self.target_app_name, p).version) for p in self.packaged_app_dirs]

    @abstractmethod
    def push(self, pyshipy_dir: Path) -> bool:
        """
        push a new target application version (a pyshipy dir)
        :param pyshipy_dir: new pyshipy to push
        :return: True on push success, False otherwise
        """
        ...

    def get_greatest_version(self) -> (VersionInfo, None):
        log.debug(f"{self.available_versions=}")
        if self.available_versions is None or len(self.available_versions) == 0:
            greatest_version = None
        else:
            greatest_version = sorted(list(self.available_versions))[-1]
        log.info(f"{greatest_version=}")
        return greatest_version

    def update(self) -> bool:
        """
        update this (the target) application (pyshipy dir)
        :return: True if successful, False otherwise
        """
        success_flag = False
        return success_flag
