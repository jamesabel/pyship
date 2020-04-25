import platform
import os
import sys
from pathlib import Path
import re
import glob
import shutil
import subprocess
import appdirs
import json
from importlib import import_module

from typeguard import typechecked
from attr import attrs, attrib
import toml
from balsa import get_logger

from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
import pyship
from pyship import get_pyship_sub_dir, get_file, extract, log_process_output, pyship_print
from pyship.launcher import calculate_launcher_metadata, load_launcher_metadata, store_launcher_metadata
from pyship.launcher import application_name as launcher_application_name

log = get_logger("pyship")


@attrs()
class PyShip:

    target_app_name = attrib(default=None)
    is_gui = attrib(default=False)
    platform_string = attrib(default="win")  # win, darwin, linux, ...
    platform_bits = attrib(default=64)
    pyproject_toml_file_path = attrib(default="pyproject.toml")
    pyship_dist_root = attrib(default="app")  # seems like as good a name as any
    cache_dir = Path(appdirs.user_cache_dir(pyship_application_name, pyship_author))

    def __attrs_post_init__(self):

        # create various dirs and paths
        if False:
            self.cache_folder = appdirs.user_cache_dir(pyship_application_name, pyship_author)
            self.pyship_dir = os.path.join(self.pyship_dist_root, get_pyship_sub_dir(self.target_app_name))
            self.python_dir = os.path.join(self.pyship_dir, "python")
            self.python_path = os.path.join(self.python_dir, "python.exe")
            os.makedirs(self.cache_folder, exist_ok=True)
            os.makedirs(self.python_dir, exist_ok=True)

        self.get_pyproject_info()
        self.launcher_metadata_filename = f"{self.target_app_name}_metadata.json"
        target_os = f"{self.platform_string}{self.platform_bits}"
        self.dist_path = Path(self.pyship_dist_root, target_os)

    def ship(self):
        self.create_launcher()
        self.create_pyshipy()

    def get_pyproject_info(self):
        log.info(f"loading {self.pyproject_toml_file_path}")
        with open(self.pyproject_toml_file_path) as f:
            pyproject = toml.load(f)
            tool_section = pyproject.get("tool")
            if tool_section:
                pyship_section = tool_section.get(pyship_application_name)
                self.target_app_name = pyship_section.get("app")

    def create_launcher(self, force: bool = False):
        """
        create the launcher executable
        :param force: set to True to force re-building the launcher (False avoids re-building the launcher if nothing has changed that would affect its functionality)
        :return: True if launcher was built
        """

        built_it = False

        # create launcher
        pyship_path_list = pyship.__path__
        if len(pyship_path_list) != 1:
            log.warning(f"not length of 1: {pyship_path_list}")
        pyship_path = pyship_path_list[0]
        launcher_module_dir = Path(pyship_path, launcher_application_name)
        launcher_source_path = os.path.join(launcher_module_dir, f"launcher.py")

        launcher_exe_filename = f"{self.target_app_name}.exe"
        launcher_exe_path = Path(self.dist_path, launcher_exe_filename)
        os.makedirs(self.dist_path, exist_ok=True)
        icon_path = os.path.join(self.target_app_name, f"{self.target_app_name}.ico")

        python_interpreter_path = sys.executable
        if python_interpreter_path is None or len(python_interpreter_path) < 1:
            log.error(f"python interpreter path not found")
        else:
            pyinstaller_exe_path = Path(Path(sys.executable).parent, "pyinstaller.exe")  # pyinstaller executable is in the same directory as the python interpreter
            if not pyinstaller_exe_path.exists():
                raise FileNotFoundError(str(pyinstaller_exe_path))
            command_line = [str(pyinstaller_exe_path), "--clean", "-F", "-i", os.path.abspath(icon_path), "-n", self.target_app_name, "--distpath", str(os.path.abspath(self.dist_path))]
            if self.is_gui:
                command_line.append("--noconsole")
            command_line.append(launcher_source_path)

            # avoid re-building launcher if its functionality wouldn't change
            launcher_metadata = calculate_launcher_metadata(launcher_module_dir, Path(icon_path))
            launcher_metadata["command_line"] = command_line
            launcher_metadata["cwd"] = pyship_path
            if force or not launcher_exe_path.exists() or launcher_metadata != load_launcher_metadata(self.dist_path, self.launcher_metadata_filename):
                try:
                    os.unlink(launcher_exe_path)
                except FileNotFoundError:
                    pass
                pyship_print(f"launcher {launcher_exe_path} building")
                pyship_print(f"{command_line}")
                launcher_run = subprocess.run(command_line, cwd=pyship_path, capture_output=True)
                store_launcher_metadata(self.dist_path, self.launcher_metadata_filename, launcher_metadata)

                # log/print pyinstaller output
                log_lines = {}
                for output_type, output_bytes in [("stdout", launcher_run.stdout), ("stderr", launcher_run.stderr)]:
                    log_lines[output_type] = log_process_output(output_type, output_bytes)

                if launcher_exe_path.exists():
                    built_it = True
                    pyship_print(f"{launcher_exe_path} built")
                else:
                    # launcher wasn't built - there was an error - so display the pyinstaller output to the user
                    for output_type, log_lines in log_lines.items():
                        pyship_print(f"{output_type}:")
                        for log_line in log_lines:
                            pyship_print(log_line)
            else:
                pyship_print(f"{launcher_exe_path} already built - no need to rebuild")

        return built_it


    def create_pyshipy(self):

        app_ver = None
        try:
            app_module = import_module(self.target_app_name)
            try:
                app_ver = app_module.__version__
            except AttributeError:
                log.error(f"your module {self.target_app_name} does not have a __version__ attribute.  Please add one.")
        except ModuleNotFoundError:
            log.error(f"your module {self.target_app_name} not found in your python environment.  Perhaps it is not installed.  Check if {self.target_app_name} is in sys.path.")
            log.info(f"{sys.path=}")

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
            get_file(zip_url, self.cache_dir, zip_file)
            pyshipy_dir = f"{self.target_app_name}_{app_ver}"
            python_dir = Path(self.dist_path, pyshipy_dir).absolute()
            extract(self.cache_dir, zip_file, python_dir)

            # Programmatically edit ._pth file, e.g. python38._pth
            # see https://github.com/pypa/pip/issues/4207
            glob_path = os.path.abspath(os.path.join(python_dir, "python*._pth"))
            pth_glob = glob.glob(glob_path)
            if pth_glob is None or len(pth_glob) != 1:
                log.critical("could not find '._pth' file at %s" % glob_path)
            else:
                pth_path = pth_glob[0]
                log.info("uncommenting import site in %s" % pth_path)
                pth_contents = open(pth_path).read()
                pth_save_path = pth_path.replace("._pth", "_orig._pth")
                shutil.move(pth_path, pth_save_path)
                pth_contents = pth_contents.replace("#import site", "import site")  # uncomment import site
                pth_contents = "..\n" + pth_contents  # add where pyship_app.py will be (one dir 'up' from python.exe)
                open(pth_path, "w").write(pth_contents)

            # install pip
            # this is how get-pip was originally obtained
            # get_pip_file = "get-pip.py"
            # get_file("https://bootstrap.pypa.io/get-pip.py", cache_folder, get_pip_file)
            get_pip_file = "get-pip.py"
            get_pip_path = os.path.join(os.path.dirname(pyship.__file__), get_pip_file)
            log.info(f"{get_pip_path}")
            cmd = ["python.exe", os.path.abspath(get_pip_path), "--no-warn-script-location"]
            log.info(f"{cmd} (cwd={python_dir})")
            subprocess.run(cmd, cwd=python_dir, shell=True)

            # upgrade pip
            cmd = ["python.exe", "-m", "pip", "install", "--no-deps", "--upgrade", "pip"]
            subprocess.run(cmd, cwd=python_dir, shell=True)

            if False:
                # TODO: load this app via flit

                # install pubapp itself into the target pubapp venv
                cmd = [pubapp_pip_path, "install", "-U", "pubapp"]
                if pubapp_dist_dir is not None:
                    cmd.extend(["-f", pubapp_dist_dir])  # get pubapp for this dir instead of PyPI
                log.info(f"{cmd}")
                subprocess.run(cmd)

                # install this local app and other requirements in the embedded python dir
                modules_to_install = [target_app_info.name, "wheel_inspect"]
                for module in modules_to_install:
                    cmd = [pubapp_pip_path, "install", "-U", module, "-f", "dist"]
                    log.info(f"{cmd}")
                    subprocess.run(cmd)

                run_nsis(target_app_info)
