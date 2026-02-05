import platform
import shutil
from pathlib import Path

from typeguard import typechecked
from balsa import get_logger

from pyship import AppInfo, pyship_print, __application_name__, CLIP_EXT
from pyship.uv_util import find_or_bootstrap_uv, uv_python_install, uv_venv_create, uv_pip_install

log = get_logger(__application_name__)


@typechecked
def create_clip(target_app_info: AppInfo, app_dir: Path, target_app_package_dist_dir: Path, cache_dir: Path, find_links: list) -> Path:
    """
    create clip (Complete Location Independent Python) environment
    clip is a stand-alone, relocatable directory that contains the entire python environment (including all libraries and the target app) needed to execute the target python application
    :param target_app_info: target app info
    :param app_dir: app gets built here (i.e. the output of this function)
    :param target_app_package_dist_dir: target app module dist dir (as a package)
    :param cache_dir: cache dir
    :param find_links: a (potentially empty) list of "find links" to add to pip invocation
    :return: path to the clip dir
    """

    clip_dir = create_base_clip(target_app_info, app_dir, cache_dir)
    assert isinstance(target_app_info.name, str)
    install_target_app(target_app_info.name, clip_dir, target_app_package_dist_dir, cache_dir, find_links)
    return clip_dir


def create_clip_file(clip_dir: Path) -> Path:
    """
    create clip file (the zipped update for the target application) from clip dir
    :param clip_dir:
    :return: path to the clip file
    """
    clip_dir_string = str(clip_dir)
    archive_name = shutil.make_archive(clip_dir_string, "zip", clip_dir_string)  # create a "zip" file of the clip dir
    return Path(clip_dir, archive_name).rename(Path(clip_dir, f"{archive_name[:-3]}{CLIP_EXT}"))  # make_archive creates a .zip, but we want a .lip


@typechecked
def create_base_clip(target_app_info: AppInfo, app_dir: Path, cache_dir: Path) -> Path:
    """
    create pyship python environment called clip using uv

    :param target_app_info: target app info
    :param app_dir: app gets built here (i.e. the output of this function)
    :param cache_dir: cache dir
    :return absolute path to created clip
    """

    python_ver_tuple = platform.python_version_tuple()
    python_version = f"{python_ver_tuple[0]}.{python_ver_tuple[1]}"

    clip_dir_name = f"{target_app_info.name}_{str(target_app_info.version)}"
    clip_dir = Path(app_dir, clip_dir_name).absolute()
    pyship_print(f'building clip {clip_dir_name} ("{clip_dir}")')

    uv_path = find_or_bootstrap_uv(cache_dir)
    uv_python_install(uv_path, python_version)
    uv_venv_create(uv_path, clip_dir, python_version)

    return clip_dir


@typechecked
def install_target_app(module_name: str, clip_dir: Path, target_app_package_dist_dir: Path, cache_dir: Path, find_links: list):
    """
    install target app as a module (and its dependencies) into clip
    :param module_name: module name
    :param clip_dir: clip dir (a relocatable venv)
    :param target_app_package_dist_dir: target app module dist dir (as a package)
    :param cache_dir: cache dir
    :param find_links: a list of "find links" to add to pip invocation
    """

    log.info(f"installing {module_name}")

    uv_path = find_or_bootstrap_uv(cache_dir)
    target_python = Path(clip_dir, "Scripts", "python.exe")

    all_find_links = list(find_links)  # copy to avoid mutating caller's list
    all_find_links.append(str(target_app_package_dist_dir.absolute()))

    uv_pip_install(uv_path, target_python, [module_name], all_find_links, upgrade=True)
