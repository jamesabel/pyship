from pathlib import Path
import sys
from importlib import import_module, reload, invalidate_caches
from pprint import pprint
from dataclasses import dataclass, fields
from abc import abstractmethod

import toml
from semver import VersionInfo
from typeguard import typechecked
from wheel_inspect import inspect_wheel

from pyship import __application_name__ as pyship_application_name, get_logger, DEFAULT_DIST_DIR_NAME, pyship_print

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

    @abstractmethod
    def load(self):
        ...


class AppInfoPyProject(AppInfo):

    def load(self, target_app_project_dir: Path = None):
        pyproject_toml_file_name = "pyproject.toml"
        pyproject_toml_file_path = Path(target_app_project_dir, pyproject_toml_file_name)

        # info from pyproject.toml overrides everything else
        log.info(f"loading {pyproject_toml_file_path} ({pyproject_toml_file_path.absolute()})")
        if pyproject_toml_file_path.exists():
            with pyproject_toml_file_path.open() as f:
                pyproject = toml.load(f)
                project_section = pyproject.get("project")
                if project_section is not None:
                    self.name = project_section.get("name", self.name)  # app name
                    self.author = project_section.get("author", self.author)  # app author

                    tool_section = pyproject.get("tool")
                    if tool_section is not None:

                        # get info from pyship section
                        # [tool.pyship]
                        pyship_app_info = tool_section.get("pyship")
                        if pyship_app_info is not None:
                            self.is_gui = pyship_app_info.get("is_gui", self.is_gui)  # False if CLI
                            self.run_on_startup = pyship_app_info.get("run_on_startup", self.run_on_startup)


class AppInfoModule(AppInfo):

    def load(self, module_path: Path = None):
        if module_path is not None and module_path.exists():
            # only temporarily put this module in the path if it's not there already
            if appended_path := module_path is not None and str(module_path) not in sys.path:
                sys.path.append(str(module_path))

            try:

                # Do as much as we can to ensure we can import a module already imported, since we re-load the test app module in our test cases (probably not something we'll see in normal
                # usage though).
                invalidate_caches()
                app_module = import_module(self.name)
                app_module = reload(app_module)  # for our test cases we need to reload a modified module (it doesn't hurt to reload an unmodified module)
                version_string = app_module.__dict__.get("__version__")
                pyship_print(f"{self.name=} {version_string=}")

                if version_string is not None:
                    self.version = VersionInfo.parse(version_string)

                self.description = app_module.__dict__.get("__doc__")
                if self.description is not None:
                    self.description = self.description.strip()

                log.info(f"got app info from {module_path}")

            except ModuleNotFoundError:
                log.info(f"{sys.path=}")
                log.info(f"module {self.name} not found")

            if appended_path:
                sys.path.remove(str(module_path))


class AppInfoWheel(AppInfo):

    def load(self, dist_path: Path = None):
        if dist_path is not None and dist_path.exists():
            wheel_info = inspect_wheel(dist_path)
            pprint(wheel_info)  # todo: STOPPED HERE


def get_app_info(target_app_project_dir: Path = None, target_app_dist_dir: Path = None, target_app_package_dir: Path = None) -> (AppInfo, None):
    """
    Get combined app info from all potential sources.
    :param target_app_project_dir: app project dir, where a pyproject.toml may reside.
    :param target_app_dist_dir: the "distribution" dir, where a wheel may reside
    :param target_app_package_dir: the package dir
    :return: an AppInfo instance
    """

    combined_app_info = AppInfo()
    for app_info_class, param in [(AppInfoPyProject, target_app_project_dir), (AppInfoModule, target_app_package_dir), (AppInfoWheel, target_app_dist_dir)]:
        app_info_obj = app_info_class(param)
        for field in fields(AppInfo):
            if value := getattr(app_info_obj, field) is not None:
                setattr(combined_app_info, field, value)

    for required_field in ["name", "author", "version"]:
        if getattr(combined_app_info, required_field) is None:
            log.error(f'"{required_field}" not defined for the target application')
            combined_app_info = None  # not sufficient to create app info
            break

    return combined_app_info


# @dataclass
# class TargetAppInfo(AppInfo):
#     """
#     get target app info
#     """
#
#     @typechecked(always=True)
#     def __init__(self, target_app_project_dir: Path = Path(), target_app_dist_dir: Path = Path(DEFAULT_DIST_DIR_NAME)):
#         """
#         get target app info
#         :param target_app_project_dir: path to target module package (directory with a __init__.py) or omit to use the current directory
#         """
#
#     @typechecked(always=True)
#     def get_module_info(self, module_path: (Path, None)):
#         """
#         get as much info as we can from the module itself
#         :param module_path:
#         :return: True if info found
#         """
#
#         log.debug(f"{module_path=}")
#         got_info = False
#
#
#         return got_info
#
#     @typechecked(always=True)
#     def get_wheel_info(self, dist_path: (Path, None)):
#         """
#         get as much info as we can from the wheel
#         :param dist_path:
#         :return: True if info found
#         """
#         log.debug(f"{dist_path=}")
#
#         return got_info
#
#     def is_complete(self):
#         return all([v is not None for v in [self.name, self.author, self.version, self.description]])
