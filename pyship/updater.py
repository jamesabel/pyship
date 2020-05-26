from abc import ABC, abstractmethod
import typing
from pathlib import Path

from semver import VersionInfo

from pyship import get_logger, __application_name__

log = get_logger(__application_name__)


class Updater(ABC):
    """
    pyship updater
    """

    @abstractmethod
    def get_available_versions(self) -> (typing.List[VersionInfo], None):
        """
        get a list of available versions
        :return: list of versions
        """
        ...

    @abstractmethod
    def push(self, pyshipy_dir: Path) -> bool:
        """
        push a new target application version (a pyshipy dir)
        :param pyshipy_dir: new pyshipy to push
        :return: True on push success, False otherwise
        """
        ...

    def get_greatest_version(self) -> (VersionInfo, None):
        versions = self.get_available_versions()
        log.debug(f"{versions=}")
        if versions is None or len(versions) == 0:
            greatest_version = None
        else:
            greatest_version = sorted(versions)[-1]
        log.info(f"{greatest_version=}")
        return greatest_version

    def update(self) -> bool:
        """
        update this (the target) application (pyshipy dir)
        :return: True if successful, False otherwise
        """
        success_flag = False
        return success_flag
