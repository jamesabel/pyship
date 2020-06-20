import os
from pathlib import Path
import shutil

import appdirs
from attr import attrs, attrib
from typeguard import typechecked

from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
from pyship import TargetAppInfo, get_logger, run_nsis, create_pyshipy, create_launcher, pyship_print, mkdirs, APP_DIR_NAME, create_shpy

log = get_logger(pyship_application_name)


@attrs()
class PyShip:

    project_dir = attrib(default=Path())  # target app project dir, e.g. the "home" directory of the project.  If None, current working directory is used.
    dist_dir = attrib(default="dist")  # filt, etc. use "dist" as the package destination directory
    find_links = attrib(default=None)  # extra dirs for pip to use for packages not yet on PyPI (e.g. under local development)
    cache_dir = Path(appdirs.user_cache_dir(pyship_application_name, pyship_author))  # used to cache things like the embedded Python zip (to keep us off the python.org servers)

    @typechecked(always=True)
    def ship_installer(self) -> (Path, None):
        """
        Perform all the steps to ship the app, including creating the installer.
        :return: the path to the created installer or None if it could not be created
        """
        pyship_print(f"{pyship_application_name} starting")

        target_app_info = TargetAppInfo(self.project_dir)
        installer_exe_path = None
        if target_app_info.is_complete():

            app_dir = Path(self.project_dir, APP_DIR_NAME, target_app_info.name).absolute()

            mkdirs(app_dir, remove_first=True)

            create_launcher(target_app_info, app_dir)  # create the OS specific launcher executable

            pyshipy_dir = create_pyshipy(target_app_info, app_dir, True, Path(self.project_dir, self.dist_dir), self.cache_dir, self.find_links)

            # run nsis
            icon_file_name = f"{target_app_info.name}.ico"
            shutil.copy2(Path(self.project_dir, icon_file_name), app_dir)  # temporarily for nsis
            installer_exe_path = run_nsis(target_app_info, target_app_info.version, app_dir)
            os.unlink(Path(app_dir, icon_file_name))

            # todo: upload the installer somewhere

            create_shpy(pyshipy_dir)  # create shpy file after installer run

            pyship_print(f"{pyship_application_name} done")
        else:
            log.error(f"insufficient app info in {target_app_info.pyproject_toml_file_path} to create application")
        return installer_exe_path

    @typechecked(always=True)
    def ship_update(self) -> (Path, None):
        """
        Create and upload an update of this target app.  The update is a zip of a pyshipy directory, with the extension .shpy.
        """
        target_app_info = TargetAppInfo(self.project_dir)
        app_dir = Path(self.project_dir, APP_DIR_NAME, target_app_info.name).absolute()
        # derived classes will take it from here and do what they need to to place the pyshipy in a place the user will get it via a call to Updater.update() ...
        return create_pyshipy(target_app_info, app_dir, True, Path(self.project_dir, self.dist_dir), self.cache_dir, self.find_links)
