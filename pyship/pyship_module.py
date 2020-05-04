import platform
import os
import sys
from pathlib import Path
import re
import glob
import shutil
import subprocess
import appdirs
from importlib import import_module
from functools import lru_cache
from semver import VersionInfo

from typeguard import typechecked
from attr import attrs, attrib

from pyship import __application_name__ as pyship_application_name, pyship_print
from pyship import __author__ as pyship_author
import pyship
from pyship import get_file, extract, TargetAppInfo, subprocess_run, python_interpreter_exes, get_logger, add_tkinter, run_nsis
from pyship.create_launcher import create_launcher

log = get_logger(pyship_application_name)


@attrs()
class PyShip:

    platform_string = attrib(default="win")  # win, darwin, linux, ...
    platform_bits = attrib(default=64)
    pyship_dist_root = attrib(default="app")  # seems like as good a name as any
    target_dist_dir = attrib(default=Path("dist"))
    cache_dir = Path(appdirs.user_cache_dir(pyship_application_name, pyship_author))

    def __attrs_post_init__(self):

        self.target_app_info = TargetAppInfo()
        if self.target_app_info.is_complete():
            target_os = f"{self.platform_string}{self.platform_bits}"
            self.dist_path = Path(self.pyship_dist_root, target_os, self.target_app_info.name).absolute()

    def ship(self):
        pyship_print(f"{pyship_application_name} starting")
        if self.target_app_info.is_complete():
            create_launcher(self.target_app_info, self.dist_path)
            pyshipy_dir = create_pyshipy(self.target_app_info, self.dist_path, self.cache_dir)
            install_target_module(self.target_app_info.name, pyshipy_dir, self.target_dist_dir.absolute())

            # remove the python interpreter we don't want
            os.unlink(Path(pyshipy_dir, python_interpreter_exes[not self.target_app_info.is_gui]))

            icon_file_name = f"{self.target_app_info.name}.ico"
            icon_path = Path(self.target_app_info.name, icon_file_name).absolute()  # this is also in create_launcher.py - make this a function somewhere
            shutil.copy2(icon_path, icon_file_name)  # temporarily for nsis
            run_nsis(self.target_app_info, get_module_version(self.target_app_info.name), pyshipy_dir)
            os.unlink(icon_file_name)

            pyship_print(f"{pyship_application_name} done")
        else:
            log.error(f"insufficient app info in {self.target_app_info.pyproject_toml_file_path} to create application")


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


@typechecked(always=True)
def create_pyshipy(target_app_info: TargetAppInfo, dist_path: Path, cache_dir: Path) -> (Path, None):
    """
    create pyship python dir
    :param target_app_info: target app info
    :param dist_path: dist path
    :param cache_dir: cache dir
    :return absolute path to pyshipy
    """

    pyshipy_dir = None
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
        get_file(zip_url, cache_dir, zip_file)
        pyshipy_dir_name = f"{target_app_info.name}_{str(app_ver)}"
        pyshipy_dir = Path(dist_path, pyshipy_dir_name).absolute()
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
