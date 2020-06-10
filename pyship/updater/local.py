"""
local pyship updater (good for testing)
"""

import typing
from pathlib import Path
from semver import VersionInfo

from pyship import Updater, ModuleInfo, copy_tree


class UpdaterLocal(Updater):

    packaged_app_dirs = set()  # directories to search for packaged app (i.e. "dist" distribution dirs)

    def get_available_versions(self) -> (typing.List[VersionInfo], None):
        """
        get available versions
        """
        [self.available_versions.add(ModuleInfo(self.target_app_name, p).version) for p in self.packaged_app_dirs]

    def get_pyshipy(self, pyshipy_source, destination_dir: Path):
        copy_tree(pyshipy_source, destination_dir, pyshipy_source.name)
