"""
local pyship updater (good for testing)
"""
from pathlib import Path
from semver import VersionInfo

from pyship import Updater, copy_tree, get_logger, __application_name__

log = get_logger(__application_name__)


class UpdaterLocal(Updater):

    packaged_app_dirs = set()  # directories to search for packaged app (i.e. "dist" distribution dirs)

    def get_available_versions(self) -> dict:
        """
        get available versions
        """
        available_versions = {}
        for p in self.packaged_app_dirs:
            # This is specific to a wheel file.  Eventually we should probably add other packaging methods
            version = None
            for file_path in p.glob("*.whl"):
                file_name_split = file_path.name.split("-")
                if len(file_name_split) > 1:
                    version = VersionInfo.parse(file_name_split[1])
                    available_versions[version] = file_path.parent
            if version is None:
                log.warning(f"no package for {self.target_app_name} found at {p}")
        log.info(f"{available_versions=}")
        return available_versions

    def get_pyshipy(self, pyshipy_source, destination_dir: Path):
        copy_tree(pyshipy_source.parent, destination_dir, pyshipy_source.name)
