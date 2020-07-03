import glob
import os
import platform
import re
import shutil
import subprocess
import tkinter
from pathlib import Path
from platform import system

from semver import VersionInfo
from typeguard import typechecked

import pyship
from pyship import TargetAppInfo, file_download, pyship_print, extract, get_logger, __application_name__, is_windows, copy_tree, subprocess_run, PYSHIPY_EXT


log = get_logger(__application_name__)


@typechecked(always=True)
def create_pyshipy(target_app_info: TargetAppInfo, app_dir: Path, remove_pth: bool, target_app_package_dist_dir: Path, cache_dir: Path, find_links: (None, list)) -> Path:
    """
    create pyshipy
    pyshipy is a stand-alone, relocatable directory that contains the entire python environment (including all libraries and the target app) needed to execute the target python application
    :param target_app_info: target app info
    :param app_dir: app gets built here (i.e. the output of this function)
    :param remove_pth: remove remove python*._pth files as a workaround (see bug URL below)
    :param target_app_package_dist_dir: target app module dist dir (as a package)
    :param cache_dir: cache dir
    :param find_links: a list of "find links" to add to pip invocation
    :return: path to the pyshipy dir
    """

    # create the pyshipy dir
    pyshipy_dir = create_base_pyshipy(target_app_info, app_dir, cache_dir)
    install_target_app(target_app_info.name, pyshipy_dir, target_app_package_dist_dir, remove_pth, find_links)
    return pyshipy_dir


def create_shpy(pyshipy_dir: Path) -> Path:
    """
    create shpy file (the zipped update for the target application) from pyshipy dir
    :param pyshipy_dir:
    :return: path to the shpy file
    """
    pyshipy_dir_string = str(pyshipy_dir)
    archive_name = shutil.make_archive(pyshipy_dir_string, "zip", pyshipy_dir_string)  # create a "zip" file of the pyshipy dir
    return Path(pyshipy_dir, archive_name).rename(Path(pyshipy_dir, f"{archive_name[:-3]}{PYSHIPY_EXT}"))  # make_archive creates a .zip, but we want a .shpy


@typechecked(always=True)
def create_base_pyshipy(target_app_info: TargetAppInfo, app_dir: Path, cache_dir: Path) -> (Path, None):
    """
    create pyship python environment called pyshipy

    :param target_app_info: target app info
    :param app_dir: app gets built here (i.e. the output of this function)
    :param cache_dir: cache dir
    :return absolute path to created pyshipy
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
    pyshipy_dir_name = f"{target_app_info.name}_{str(target_app_info.version)}"
    pyshipy_dir = Path(app_dir, pyshipy_dir_name).absolute()
    pyship_print(f"creating application {pyshipy_dir_name} ({pyshipy_dir})")
    extract(cache_dir, zip_file, pyshipy_dir)

    # Programmatically edit ._pth file, e.g. python38._pth
    # see https://github.com/pypa/pip/issues/4207
    # todo: refactor to use Path
    glob_path = os.path.abspath(os.path.join(pyshipy_dir, "python*._pth"))
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
    log.info(f"{get_pip_path}")
    cmd = ["python.exe", os.path.abspath(get_pip_path), "--no-warn-script-location"]
    log.info(f"{cmd} (cwd={pyshipy_dir})")
    subprocess.run(cmd, cwd=pyshipy_dir, shell=True)  # todo: use subprocess_run

    # upgrade pip
    cmd = ["python.exe", "-m", "pip", "install", "--no-deps", "--upgrade", "pip"]
    subprocess.run(cmd, cwd=pyshipy_dir, shell=True)  # todo: use subprocess_run

    # the embedded Python doesn't ship with tkinter, so add it to pyshipy
    # https://stackoverflow.com/questions/37710205/python-embeddable-zip-install-tkinter
    if is_windows():
        python_base_install_dir = Path(tkinter.__file__).parent.parent.parent
        copy_tree(Path(python_base_install_dir), pyshipy_dir, "tcl")  # tcl dir
        copy_tree(Path(python_base_install_dir, "Lib"), Path(pyshipy_dir, "Lib", "site-packages"), "tkinter")  # tkinter dir
        # dlls
        for file_name in ["_tkinter.pyd", "tcl86t.dll", "tk86t.dll"]:
            shutil.copy2(str(Path(python_base_install_dir, "DLLs", file_name)), str(pyshipy_dir))
    else:
        log.fatal(f"Unsupported OS: {system()}")

    return pyshipy_dir


@typechecked(always=True)
def install_target_app(module_name: str, python_env_dir: Path, target_app_package_dist_dir: Path, remove_pth: bool, find_links: (None, list)):
    """
    install target app as a module (and its dependencies) into pyshipy
    :param module_name: module name
    :param python_env_dir: venv or pyshipy dir
    :param target_app_package_dist_dir: target app module dist dir (as a package)
    :param remove_pth: remove remove python*._pth files as a workaround (see bug URL below)
    :param find_links: a list of "find links" to add to pip invocation
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
    cmd = [str(Path(python_env_dir, "python.exe")), "-m", "pip", "install", "-U", module_name, "--no-warn-script-location"]

    if find_links is None:
        find_links = []

    find_links.append(str(target_app_package_dist_dir.absolute()))

    # for testing, to keep off the main pypi
    pypi_local = os.getenv("PYPILOCAL")
    if pypi_local is not None and len(pypi_local) > 0:

        # todo: investigate while this doesn't work - can't find all the modules
        # cmd.append("--no-index")  # stay off pypi

        find_links.append(pypi_local)

    for find_link in find_links:
        cmd.extend(["-f", str(find_link)])

    pyship_print(str(cmd))
    subprocess_run(cmd, cwd=python_env_dir, mute_output=False)


@typechecked(always=True)
def version_from_pyshipy_zip(target_app_name: str, candidate_pyshipy_zip: str) -> (VersionInfo, None):
    """
    Tests if a string is a pyshipy zip string.  If so, extract the version from a pyshipy zip string.  If the string is not a valid pyshipy zip string, return None.
    Example: a pyshipy zip string of "abc_1.2.3.zip" for app "abc" returns VersionInfo of 1.2.3.
    :param target_app_name: target app name
    :param candidate_pyshipy_zip: candidate pyshipy app zip string to try to get the version from
    :return: version or None if not a successful parse for a pyshipy zip string
    """
    version = None
    if candidate_pyshipy_zip.startswith(target_app_name):
        version_string = candidate_pyshipy_zip[len(target_app_name) :]
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
