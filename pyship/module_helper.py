import shutil
import sys
from functools import lru_cache
from importlib import import_module
from pathlib import Path

from semver import VersionInfo
from typeguard import typechecked

from pyship import pyship_print, subprocess_run, __application_name__, get_logger

log = get_logger(__application_name__)


@typechecked(always=True)
def install_target_module(module_name: str, pyshipy_dir: Path, target_dist_dir: Path):
    """
    install target module and its dependencies into pyshipy
    :param module_name: module name
    :param pyshipy_dir: pyshipy dir
    :param target_dist_dir: target module dist dir
    :return:
    """

    # install this local app in the embedded python dir
    pyship_print(f"installing {module_name} into {pyshipy_dir}")

    # remove python*._pth
    # https://github.com/PythonCharmers/python-future/issues/411
    pth_glob_list = [p for p in Path(pyshipy_dir).glob("python*._pth")]
    if len(pth_glob_list) == 1:
        pth_path = str(pth_glob_list[0])
        pth_save_path = pth_path.replace("._pth", "._future_bug_pth")
        shutil.move(pth_path, pth_save_path)

        # install the target module (and its dependencies)
        cmd = [str(Path(pyshipy_dir, "python.exe")), "-m", "pip", "install", "-U", module_name, "-f", str(target_dist_dir), "--no-warn-script-location"]
        subprocess_run(cmd, cwd=pyshipy_dir)
    else:
        log.error(f"unexpected {pth_glob_list=} found at {pyshipy_dir=}")


@typechecked(always=True)
@lru_cache()
def get_module_version(module_name: str) -> (VersionInfo, None):
    app_ver = None
    try:
        app_module = import_module(module_name)
        try:
            app_ver = VersionInfo.parse(app_module.__version__)
        except AttributeError:
            log.error(f"your module {module_name} does not have a __version__ attribute.  Please add one.")
    except ModuleNotFoundError:
        log.info(f"{sys.path=}")
        log.error(f"your module {module_name} not found in your python environment.  Perhaps it is not installed.  Check if {module_name} is in sys.path.")
    return app_ver