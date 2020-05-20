import os
from pathlib import Path
import shutil

import appdirs
from attr import attrs, attrib
from typeguard import typechecked

from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
from pyship import TargetAppInfo, get_logger, run_nsis, pyship_print, create_base_pyshipy, create_launcher, pyship_print, subprocess_run, mkdirs, ModuleInfo

log = get_logger(pyship_application_name)


@attrs()
class PyShip:

    platform_string = attrib(default="win")  # win, darwin, linux, ...
    platform_bits = attrib(default=64)
    target_app_dir = attrib(default=Path())  # if None, current working directory is used
    pyship_dist_root = attrib(default="app")  # seems like as good a name as any
    target_dist_dir = attrib(default=Path("dist"))
    cache_dir = Path(appdirs.user_cache_dir(pyship_application_name, pyship_author))

    def __attrs_post_init__(self):

        self.target_app_info = TargetAppInfo(self.target_app_dir)
        if self.target_app_info.is_complete():
            self.frozen_app_path = Path(self.pyship_dist_root, self.get_target_os(), self.target_app_info.name).absolute()

    def get_target_os(self):
        return f"{self.platform_string}{self.platform_bits}"

    def ship(self):
        pyship_print(f"{pyship_application_name} starting")
        if self.target_app_info.is_complete():

            module_info = ModuleInfo(self.target_app_info.name, self.target_app_info.target_app_dir)
            target_app_version = module_info.version

            create_launcher(self.target_app_info, self.frozen_app_path)  # create the OS specific launcher executable

            pyshipy_dir = create_base_pyshipy(self.target_app_info, self.frozen_app_path, self.cache_dir)  # create the base pyshipy

            install_target_app(self.target_app_info.name, pyshipy_dir, package_dist_dir, True)

            icon_file_name = f"{self.target_app_info.name}.ico"
            icon_path = Path(self.target_app_info.name, icon_file_name).absolute()  # this is also in create_launcher.py - make this a function somewhere
            shutil.copy2(icon_path, icon_file_name)  # temporarily for nsis
            run_nsis(self.target_app_info, target_app_version, pyshipy_dir)
            os.unlink(icon_file_name)

            pyship_print(f"{pyship_application_name} done")
        else:
            log.error(f"insufficient app info in {self.target_app_info.pyproject_toml_file_path} to create application")


@typechecked(always=True)
def install_target_app(module_name: str, python_env_dir: Path, target_app_package_dist_dir: Path, remove_pth: bool = False):
    """
    install target app as a module (and its dependencies) into pyshipy
    :param module_name: module name
    :param python_env_dir: venv or pyshipy dir
    :param target_app_package_dist_dir: target app module dist dir (as a package)
    :param remove_pth: remove remove python*._pth files as a workaround (see bug URL below)
    """

    # install this local app in the embedded python dir
    pyship_print(f"installing {module_name} into {python_env_dir}")

    if remove_pth:
        # remove python*._pth
        # https://github.com/PythonCharmers/python-future/issues/411
        pth_glob_list = [p for p in Path(python_env_dir).glob("python*._pth")]
        if len(pth_glob_list) == 1:
            pth_path = str(pth_glob_list[0])
            pth_save_path = pth_path.replace("._pth", "._future_bug_pth")
            shutil.move(pth_path, pth_save_path)
        else:
            log.error(f"unexpected {pth_glob_list=} found at {python_env_dir=}")

    # install the target module (and its dependencies)
    cmd = [str(Path(python_env_dir, "python.exe")), "-m", "pip", "install", "-U", module_name, "-f", str(target_app_package_dist_dir), "--no-warn-script-location"]
    subprocess_run(cmd, cwd=python_env_dir)
