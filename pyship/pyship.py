from pathlib import Path

import appdirs
from attr import attrs
from typeguard import typechecked

from pyshipupdate import mkdirs
from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
from pyship import AppInfo, get_logger, run_nsis, create_clip, create_launcher, pyship_print, APP_DIR_NAME, create_clip_file, DEFAULT_DIST_DIR_NAME, get_app_info, PyShipCloud

log = get_logger(pyship_application_name)


@attrs(auto_attribs=True)
class PyShip:

    project_dir: Path = Path()  # target app project dir, e.g. the "home" directory of the project.  If None, current working directory is used.
    dist_dir: Path = Path(DEFAULT_DIST_DIR_NAME)  # many packaging tools (e.g filt, etc.) use "dist" as the package destination directory
    find_links: list = []  # extra dirs for pip to use for packages not yet on PyPI (e.g. under local development)
    cache_dir: Path = Path(appdirs.user_cache_dir(pyship_application_name, pyship_author))  # used to cache things like the embedded Python zip (to keep us off the python.org servers)
    cloud_access: PyShipCloud = None

    @typechecked(always=True)
    def ship_installer(self) -> (Path, None):
        """
        Perform all the steps to ship the app, including creating the installer.
        :return: the path to the created installer or None if it could not be created
        """
        pyship_print(f"{pyship_application_name} starting")

        target_app_info = get_app_info(self.project_dir, self.dist_dir)

        installer_exe_path = None
        if self.project_dir is None:
            log.error(f"{self.project_dir=}")
        elif target_app_info is None:
            log.error(f"{target_app_info=}")
        elif target_app_info.name is None:
            log.error(f"{target_app_info.name=}")
        else:
            app_dir = Path(self.project_dir, APP_DIR_NAME, target_app_info.name).absolute()

            mkdirs(app_dir, remove_first=True)

            create_launcher(target_app_info, app_dir)  # create the OS specific launcher executable

            clip_dir = create_clip(target_app_info, app_dir, True, Path(self.project_dir, self.dist_dir), self.cache_dir, self.find_links)

            clip_file_path = create_clip_file(clip_dir)  # create clip file
            installer_exe_path = run_nsis(target_app_info, target_app_info.version, app_dir)  # create installer

            if self.cloud_access is None:
                log.info(f"no cloud access provided - will not attempt upload")
            else:
                self.cloud_access.upload(installer_exe_path)  # create and upload installer
                self.cloud_access.upload(clip_file_path)  # create and upload clip file

            pyship_print(f"{pyship_application_name} done")

        return installer_exe_path

    @typechecked(always=True)
    def ship_update(self) -> (Path, None):
        """
        Create and upload an update of this target app.  The update is a zip of a clip directory, with the extension .clip.
        """
        target_app_info = AppInfo()
        target_app_info.setup_paths(self.project_dir)
        app_dir = Path(self.project_dir, APP_DIR_NAME, target_app_info.name).absolute()
        # derived classes will take it from here and do what they need to to place the clip in a place the user will get it via a call to Updater.update() ...
        return create_clip(target_app_info, app_dir, True, Path(self.project_dir, self.dist_dir), self.cache_dir, self.find_links)
