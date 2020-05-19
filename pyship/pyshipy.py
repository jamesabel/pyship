import glob
import os
import platform
import re
import shutil
import subprocess
import sys
import tkinter
from pathlib import Path

from typeguard import typechecked

import pyship
from pyship import TargetAppInfo, file_download, pyship_print, extract, get_logger, get_module_version, __application_name__, is_windows
from pyship.os_util import copy_tree

log = get_logger(__application_name__)


@typechecked(always=True)
def create_pyshipy(target_app_info: TargetAppInfo, app_path_output: Path, cache_dir: Path, target_app_source_dir: (Path, None)) -> (Path, None):
    """
    create pyship python dir
    :param target_app_info: target app info
    :param app_path_output: app gets built here (i.e. the output of this function)
    :param cache_dir: cache dir
    :param target_app_source_dir: target application source dir (use if target app not the current dir nor installed into the venv we're executing from) (input)
    :return absolute path to created pyshipy
    """

    pyshipy_dir = None

    if target_app_source_dir is not None:
        # Usually pyship is executed in the parent directory of the target application module.  If it isn't, set this dir to the target application module's parent dir.
        sys.path.append(str(target_app_source_dir.absolute()))

    app_ver = get_module_version(target_app_info.name)

    if app_ver is not None:

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
        pyshipy_dir_name = f"{target_app_info.name}_{str(app_ver)}"
        pyshipy_dir = Path(app_path_output, pyshipy_dir_name).absolute()
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
        subprocess.run(cmd, cwd=pyshipy_dir, shell=True)

        # upgrade pip
        cmd = ["python.exe", "-m", "pip", "install", "--no-deps", "--upgrade", "pip"]
        subprocess.run(cmd, cwd=pyshipy_dir, shell=True)

        # install tkinter (it doesn't come with embedded python)
        add_tkinter(pyshipy_dir)

    return pyshipy_dir


@typechecked(always=True)
def add_tkinter(pyshipy: Path):
    # the embedded Python doesn't ship with tkinter, so add it to pyshipy
    # https://stackoverflow.com/questions/37710205/python-embeddable-zip-install-tkinter

    if is_windows():
        python_base_install_dir = Path(tkinter.__file__).parent.parent.parent

        copy_tree(Path(python_base_install_dir), pyshipy, "tcl")  # tcl dir
        copy_tree(Path(python_base_install_dir, "Lib"), Path(pyshipy, "Lib", "site-packages"), "tkinter")  # tkinter dir

        # dlls
        for file_name in ["_tkinter.pyd", "tcl86t.dll", "tk86t.dll"]:
            shutil.copy2(str(Path(python_base_install_dir, "DLLs", file_name)), str(pyshipy))