import glob
import os
import platform
import re
import shutil
import subprocess
import tkinter
from pathlib import Path
from platform import system
import inspect

from semver import VersionInfo
from typeguard import typechecked

from pyshipupdate import is_windows, copy_tree
import pyship
import pyship.patch.pyship_patch
from pyship import AppInfo, file_download, pyship_print, extract, get_logger, __application_name__, subprocess_run, CLIP_EXT


log = get_logger(__application_name__)


@typechecked(always=True)
def create_clip(target_app_info: AppInfo, app_dir: Path, remove_pth: bool, target_app_package_dist_dir: Path, cache_dir: Path, find_links: list) -> Path:
    """
    create clip (Complete Location Independent Python) environment
    clip is a stand-alone, relocatable directory that contains the entire python environment (including all libraries and the target app) needed to execute the target python application
    :param target_app_info: target app info
    :param app_dir: app gets built here (i.e. the output of this function)
    :param remove_pth: remove remove python*._pth files as a workaround (see bug URL below)
    :param target_app_package_dist_dir: target app module dist dir (as a package)
    :param cache_dir: cache dir
    :param find_links: a (potentially empty) list of "find links" to add to pip invocation
    :return: path to the clip dir
    """

    # create the clip dir
    clip_dir = create_base_clip(target_app_info, app_dir, cache_dir)
    install_target_app(target_app_info.name, clip_dir, target_app_package_dist_dir, remove_pth, find_links)
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


@typechecked(always=True)
def create_base_clip(target_app_info: AppInfo, app_dir: Path, cache_dir: Path) -> (Path, None):
    """
    create pyship python environment called clip

    :param target_app_info: target app info
    :param app_dir: app gets built here (i.e. the output of this function)
    :param cache_dir: cache dir
    :return absolute path to created clip
    """

    # use project's Python (in this venv) to determine target Python version
    python_ver_str = platform.python_version()
    python_ver_tuple = platform.python_version_tuple()

    # get the embedded python interpreter
    base_patch_str = re.search(r"([0-9]+)", python_ver_tuple[2]).group(1)
    # version but with numbers only and not the extra release info (e.g. b, rc, etc.)
    ver_base_str = f"{python_ver_tuple[0]}.{python_ver_tuple[1]}.{base_patch_str}"
    zip_file = Path(f"python-{python_ver_str}-embed-amd64.zip")
    zip_url = f"https://www.python.org/ftp/python/{ver_base_str}/{zip_file}"
    file_download(zip_url, cache_dir, zip_file)
    clip_dir_name = f"{target_app_info.name}_{str(target_app_info.version)}"
    clip_dir = Path(app_dir, clip_dir_name).absolute()
    pyship_print(f"building clip {clip_dir_name} ({clip_dir})")
    extract(cache_dir, zip_file, clip_dir)

    # Programmatically edit ._pth file, e.g. python38._pth
    # see https://github.com/pypa/pip/issues/4207
    # todo: refactor to use Path
    glob_path = os.path.abspath(os.path.join(clip_dir, "python*._pth"))
    pth_glob = glob.glob(glob_path)
    if pth_glob is None or len(pth_glob) != 1:
        log.critical("could not find '._pth' file at %s" % glob_path)
    else:
        pth_path = pth_glob[0]
        log.info("uncommenting import site in %s" % pth_path)
        pth_contents = open(pth_path).read()
        pth_save_path = pth_path.replace("._pth", "._pip_bug_pth")
        shutil.move(pth_path, pth_save_path)
        pth_contents = pth_contents.replace("#import site", "import site")  # uncomment import site
        pth_contents = "..\n" + pth_contents  # add where pyship_main.py will be (one dir 'up' from python.exe)
        open(pth_path, "w").write(pth_contents)

    # install pip
    # this is how get-pip was originally obtained
    # get_pip_file = "get-pip.py"
    # get_file("https://bootstrap.pypa.io/get-pip.py", cache_folder, get_pip_file)
    get_pip_file = "get-pip.py"
    get_pip_path = os.path.join(os.path.dirname(pyship.__file__), get_pip_file)
    log.info(f"{get_pip_path=}")
    get_pip_cmd = ["python.exe", os.path.abspath(get_pip_path), "--no-warn-script-location"]
    log.info(f"{get_pip_cmd=}")
    subprocess.run(get_pip_cmd, cwd=clip_dir, capture_output=True, shell=True, check=True)  # subprocess_run uses typeguard and we don't have that yet so just use subprocess.run

    # upgrade pip
    pip_upgrade_cmd = ["python.exe", "-m", "pip", "install", "--no-deps", "--upgrade", "pip"]
    log.info(f"{pip_upgrade_cmd=}")
    subprocess.run(pip_upgrade_cmd, cwd=clip_dir, capture_output=True, shell=True, check=True)  # subprocess_run uses typeguard and we don't have that yet so just use subprocess.run

    # the embedded Python doesn't ship with tkinter, so add it to clip
    # https://stackoverflow.com/questions/37710205/python-embeddable-zip-install-tkinter
    if is_windows():
        python_base_install_dir = Path(tkinter.__file__).parent.parent.parent
        copy_tree(Path(python_base_install_dir), clip_dir, "tcl")  # tcl dir
        copy_tree(Path(python_base_install_dir, "Lib"), Path(clip_dir, "Lib", "site-packages"), "tkinter")  # tkinter dir
        # dlls
        for file_name in ["_tkinter.pyd", "tcl86t.dll", "tk86t.dll"]:
            shutil.copy2(str(Path(python_base_install_dir, "DLLs", file_name)), str(clip_dir))
    else:
        log.fatal(f"Unsupported OS: {system()}")

    # write out patch files
    Path(clip_dir, "pyship_patch.pth").write_text("import pyship_patch")  # this causes the pyship_patch.py to be loaded and therefore executed
    patch_string = f"{inspect.getsource(pyship.patch.pyship_patch.pyship_patch)}\n\npyship_patch()\n"
    Path(clip_dir, "pyship_patch.py").write_text(patch_string)  # due to the above, this file gets executed at Python interpreter startup

    return clip_dir


@typechecked(always=True)
def install_target_app(module_name: str, python_env_dir: Path, target_app_package_dist_dir: Path, remove_pth: bool, find_links: list):
    """
    install target app as a module (and its dependencies) into clip
    :param module_name: module name
    :param python_env_dir: venv or clip dir
    :param target_app_package_dist_dir: target app module dist dir (as a package)
    :param remove_pth: remove remove python*._pth files as a workaround (see bug URL below)
    :param find_links: a list of "find links" to add to pip invocation
    """

    # install this local app in the embedded python dir
    log.info(f"installing {module_name}")

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
    cmd = [str(Path(python_env_dir, "python.exe")), "-m", "pip", "install", "-U", module_name, "--no-warn-script-location"]

    find_links.append(str(target_app_package_dist_dir.absolute()))

    for find_link in find_links:
        cmd.extend(["-f", f'file://{str(find_link)}'])

    subprocess_run(cmd, python_env_dir)


@typechecked(always=True)
def version_from_clip_zip(target_app_name: str, candidate_clip_zip: str) -> (VersionInfo, None):
    """
    Tests if a string is a clip zip string.  If so, extract the version from a clip zip string.  If the string is not a valid clip zip string, return None.
    Example: a clip zip string of "abc_1.2.3.zip" for app "abc" returns VersionInfo of 1.2.3.
    :param target_app_name: target app name
    :param candidate_clip_zip: candidate clip app zip string to try to get the version from
    :return: version or None if not a successful parse for a clip zip string
    """
    version = None
    if candidate_clip_zip.startswith(target_app_name):
        version_string = candidate_clip_zip[len(target_app_name):]
        for extension in [".zip", ".7z"]:
            if version is None and version_string.endswith(extension):
                version_string = version_string[: -len(extension)]  # remove extension
                if version_string.startswith("_"):
                    try:
                        version = VersionInfo.parse(version_string[1:])  # pass over the "_"
                    except IndexError as e:
                        pass
                    except TypeError as e:
                        pass
                    except ValueError as e:
                        pass
    return version
