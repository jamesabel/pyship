import os
from pathlib import Path
import shutil

import appdirs
from attr import attrs, attrib

from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
from pyship import TargetAppInfo, get_logger, run_nsis, pyship_print, create_pyshipy, create_launcher, install_target_module, get_module_version

log = get_logger(pyship_application_name)


@attrs()
class PyShip:

    platform_string = attrib(default="win")  # win, darwin, linux, ...
    platform_bits = attrib(default=64)
    target_app_dir = attrib(default=None)  # if None, current working directory is used
    pyship_dist_root = attrib(default="app")  # seems like as good a name as any
    target_dist_dir = attrib(default=Path("dist"))
    cache_dir = Path(appdirs.user_cache_dir(pyship_application_name, pyship_author))

    def __attrs_post_init__(self):

        self.target_app_info = TargetAppInfo()
        if self.target_app_info.is_complete():
            self.app_path = Path(self.pyship_dist_root, self.get_target_os(), self.target_app_info.name).absolute()

    def get_target_os(self):
        return f"{self.platform_string}{self.platform_bits}"

    def ship(self):
        pyship_print(f"{pyship_application_name} starting")
        if self.target_app_info.is_complete():
            create_launcher(self.target_app_info, self.app_path)
            pyshipy_dir = create_pyshipy(self.target_app_info, self.app_path, self.cache_dir, self.target_app_dir)
            install_target_module(self.target_app_info.name, pyshipy_dir, self.target_dist_dir.absolute())

            icon_file_name = f"{self.target_app_info.name}.ico"
            icon_path = Path(self.target_app_info.name, icon_file_name).absolute()  # this is also in create_launcher.py - make this a function somewhere
            shutil.copy2(icon_path, icon_file_name)  # temporarily for nsis
            run_nsis(self.target_app_info, get_module_version(self.target_app_info.name), pyshipy_dir)
            os.unlink(icon_file_name)

            pyship_print(f"{pyship_application_name} done")
        else:
            log.error(f"insufficient app info in {self.target_app_info.pyproject_toml_file_path} to create application")
