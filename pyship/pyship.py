import os
from pathlib import Path
import shutil

import appdirs
from attr import attrs, attrib

from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
from pyship import TargetAppInfo, get_logger, run_nsis, create_pyshipy, create_launcher, pyship_print, mkdirs, APP_DIR_NAME

log = get_logger(pyship_application_name)


@attrs()
class PyShip:

    project_dir = attrib(default=Path())  # target app project dir, e.g. the "home" directory of the project.  If None, current working directory is used.
    dist_dir = attrib(default="dist")  # filt, etc. use "dist" as the package destination directory
    find_links = attrib(default=None)  # extra dirs for pip to use for packages not yet on PyPI (e.g. under local development)
    cache_dir = Path(appdirs.user_cache_dir(pyship_application_name, pyship_author))  # used to cache things like the embedded Python zip (to keep us off the python.org servers)
    target_app_info = None
    app_dir = None  # where the full, frozen application will be built

    def ship_app(self):
        """
        Perform all the steps to ship the app, including creating the installer.
        """
        pyship_print(f"{pyship_application_name} starting")

        self.target_app_info = TargetAppInfo(self.project_dir)
        if self.target_app_info.is_complete():

            self.app_dir = Path(self.project_dir, APP_DIR_NAME, self.target_app_info.name).absolute()

            mkdirs(self.app_dir, remove_first=True)

            create_launcher(self.target_app_info, self.app_dir)  # create the OS specific launcher executable

            create_pyshipy(self.target_app_info, self.app_dir, True, Path(self.project_dir, self.dist_dir), self.cache_dir, self.find_links)

            # run nsis
            icon_file_name = f"{self.target_app_info.name}.ico"
            shutil.copy2(Path(self.project_dir, icon_file_name), self.app_dir)  # temporarily for nsis
            run_nsis(self.target_app_info, self.target_app_info.version, self.app_dir)
            os.unlink(Path(self.app_dir, icon_file_name))

            # todo: upload the installer somewhere

            pyship_print(f"{pyship_application_name} done")
        else:
            log.error(f"insufficient app info in {self.target_app_info.pyproject_toml_file_path} to create application")

    def ship_update(self):
        """
        Create and upload an update of this target app.  The update is a zip of a pyshipy directory, with the extension .shpy.
        """
        # todo: code this
        pass
