"""
local pyship updater (good for testing)
"""
from pathlib import Path
from semver import VersionInfo

from pyship import Updater, copy_tree, get_logger, __application_name__

log = get_logger(__application_name__)


class UpdaterLocal(Updater):

    app_dirs = set()  # directories to search for pyshipys

    def get_available_versions(self) -> (dict, None):
        """
        get available versions
        """
        if self.target_app_name is None or len(self.target_app_name) == 0:
            log.warning(f"no target app name")
            available_versions = None
        else:
            available_versions = {}
            for app_dir in self.app_dirs:
                glob_string = f"{self.target_app_name}_*"
                glob_dirs = [p for p in app_dir.glob(glob_string) if p.is_dir()]
                if len(glob_dirs) == 1:
                    pyshipy_dir = glob_dirs[0]
                    if pyshipy_dir.name.startswith(self.target_app_name):
                        version_string = pyshipy_dir.name.replace(f"{self.target_app_name}", "")[1:]  # pyshipy has a character (underscore) between the target app name and the version
                        try:
                            version = VersionInfo.parse(version_string)
                            available_versions[version] = pyshipy_dir
                        except IndexError:
                            log.warning(f'version string format error "{version_string}"')
                    else:
                        log.warning(f'"{str(pyshipy_dir)}" does not start with {self.target_app_name}')
                else:
                    log.warning(f'glob {app_dir} {glob_string} yielded {len(glob_dirs)} results, expected exactly 1')
                    log.warning(glob_dirs)

            log.info(f"{available_versions=}")
        return available_versions

    def install_pyshipy(self, version: VersionInfo, app_dir: Path) -> bool:
        """
        install a particular version of pyshipy
        :param version: version to install
        :param app_dir: app dir
        :return: True on success, False otherwise
        """
        available_versions = self.get_available_versions()
        log.info(f"{available_versions=}")
        if version in available_versions:
            pyshipy = available_versions[version]
            copy_tree(pyshipy.parent, app_dir, pyshipy.name)
            success_flag = True
        else:
            log.warning(f"could not find version {version}")
            success_flag = False
        log.info(f"{success_flag=}")
        return success_flag
