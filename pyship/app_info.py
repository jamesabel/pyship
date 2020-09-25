from pathlib import Path
import sys
from importlib import import_module, reload, invalidate_caches
from pprint import pprint
from dataclasses import dataclass

import toml
from semver import VersionInfo
from typeguard import typechecked
from wheel_inspect import inspect_wheel

from pyship import __application_name__ as pyship_application_name
from pyship import get_logger, pyship_print

log = get_logger(pyship_application_name)


@dataclass
class AppInfo:
    name: str = None
    author: str = None
    version: VersionInfo = None
    is_gui: bool = None
    url: str = None
    description: str = None
    run_on_startup: bool = None
    project_dir: Path = None
    python_exe_path: Path = None
    pyship_installed_package_dir: Path = None

    def setup_paths(self, target_app_project_dir: Path):
        self.project_dir = target_app_project_dir
        self.python_exe_path = Path(self.project_dir, "venv", "Scripts", "python.exe")
        self.pyship_installed_package_dir = Path(self.project_dir, "venv", "Lib", "site-packages", pyship_application_name)


@typechecked(always=True)
def get_app_info_py_project(app_info: AppInfo, target_app_project_dir: Path = None) -> AppInfo:
    pyproject_toml_file_name = "pyproject.toml"
    pyproject_toml_file_path = Path(target_app_project_dir, pyproject_toml_file_name)

    # info from pyproject.toml overrides everything else
    log.info(f"loading {pyproject_toml_file_path} ({pyproject_toml_file_path.absolute()})")
    if pyproject_toml_file_path.exists():
        with pyproject_toml_file_path.open() as f:
            pyproject = toml.load(f)
            project_section = pyproject.get("project")
            if project_section is not None:
                app_info.name = project_section.get("name")  # app name
                app_info.author = project_section.get("author")  # app author

                tool_section = pyproject.get("tool")
                if tool_section is not None:

                    # get info from pyship section
                    # [tool.pyship]
                    pyship_app_info = tool_section.get("pyship")
                    if pyship_app_info is not None:
                        app_info.is_gui = pyship_app_info.get("is_gui")  # False if CLI
                        app_info.run_on_startup = pyship_app_info.get("run_on_startup")
    return app_info


# @typechecked(always=True)
# def get_app_info_module(app_info: AppInfo, module_path: Path = None) -> AppInfo:
#     if module_path is not None and module_path.exists():
#         # only temporarily put this module in the path if it's not there already
#         if appended_path := module_path is not None and str(module_path) not in sys.path:
#             sys.path.append(str(module_path))
#
#         try:
#
#             # Do as much as we can to ensure we can import a module already imported, since we re-load the test app module in our test cases (probably not something we'll see in normal
#             # usage though).
#             invalidate_caches()
#             app_module = import_module(app_info.name)
#             app_module = reload(app_module)  # for our test cases we need to reload a modified module (it doesn't hurt to reload an unmodified module)
#
#             author_string = app_module.__dict__.get("__author__")
#             if author_string is not None:
#                 app_info.author = author_string
#                 pyship_print(f"author={author_string}")
#
#             version_string = app_module.__dict__.get("__version__")
#             if version_string is not None:
#                 pyship_print(f"version={version_string}")
#                 app_info.version = VersionInfo.parse(version_string)
#
#             app_info.description = app_module.__dict__.get("__doc__")
#             if app_info.description is not None:
#                 app_info.description = app_info.description.strip()
#
#             log.info(f"got app info from {module_path}")
#
#         except ModuleNotFoundError:
#             log.info(f"{sys.path=}")
#             log.info(f"module {app_info.name} not found")
#
#         if appended_path:
#             sys.path.remove(str(module_path))
#     return app_info


@typechecked(always=True)
def get_app_info_wheel(app_info: AppInfo, dist_path: Path) -> AppInfo:
    if dist_path is not None and dist_path.exists():
        wheel_info = inspect_wheel(dist_path)
        metadata = wheel_info["dist_info"]["metadata"]
        app_info.name = metadata.get("name")
        app_info.version = VersionInfo.parse(metadata.get("version"))
        app_info.author = metadata.get("author")
        app_info.description = metadata.get("summary", "")  # called description in setup.py
    return app_info


@typechecked(always=True)
def get_app_info(target_app_project_dir: Path, target_app_dist_dir: Path) -> (AppInfo, None):
    """
    Get combined app info from all potential sources.
    :param name: target application name (optional)
    :param target_app_project_dir: app project dir, e.g. where a pyproject.toml may reside. (optional)
    :param target_app_dist_dir: the "distribution" dir, e.g. where a wheel may reside (optional)
    :return: an AppInfo instance
    """

    app_info = AppInfo()
    app_info.setup_paths(target_app_project_dir)

    get_app_info_py_project(app_info, target_app_project_dir)

    wheel_list = list(target_app_dist_dir.glob(f"{app_info.name}*.whl"))
    if len(wheel_list) == 0:
        log.error(f"no wheel at {target_app_dist_dir}")
    elif len(wheel_list) > 1:
        log.error(f"multiple wheels at {target_app_dist_dir} : {wheel_list}")
    else:
        app_info = get_app_info_wheel(app_info, wheel_list[0])

        if app_info.is_gui is None:
            # todo: automatically guess if the app is a GUI app by looking for PyQt, etc.
            is_gui_guess = False

            log.warning(f"is_gui has not been set by the user (e.g. in pyproject.toml) - assuming {is_gui_guess}")
            app_info.is_gui = is_gui_guess

        # check that we have the minimum fields filled in
        for required_field in ["name", "author", "version"]:
            if (attribute_value := getattr(app_info, required_field)) is None:
                log.error(f'"{required_field}" not defined for the target application')
                app_info = None  # not sufficient to create app info
                break
            else:
                pyship_print(f"{required_field}={attribute_value}")

    return app_info
