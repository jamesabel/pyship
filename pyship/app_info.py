from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Union

import toml
from semver import VersionInfo
from typeguard import typechecked
from wheel_inspect import inspect_wheel
from balsa import get_logger

from pyship import __application_name__ as pyship_application_name
from pyship import pyship_print, PyshipInsufficientAppInfo, NullPath

log = get_logger(pyship_application_name)


@dataclass
class AppInfo:
    name: Union[str, None] = None
    author: Union[str, None] = None
    version: Union[VersionInfo, None] = None
    is_gui: Union[bool, None] = None
    url: Union[str, None] = None
    description: Union[str, None] = None
    run_on_startup: Union[bool, None] = None

    # these will be filled in
    project_dir: Path = NullPath()
    python_exe_path: Path = NullPath()
    pyship_installed_package_dir: Path = NullPath()

    icon_file_name: Union[str, None] = None

    def setup_paths(self, target_app_project_dir: Path):
        self.project_dir = target_app_project_dir
        self.python_exe_path = Path(self.project_dir, "venv", "Scripts", "python.exe")
        self.pyship_installed_package_dir = Path(self.project_dir, "venv", "Lib", "site-packages", pyship_application_name)


@typechecked
def get_app_info_py_project(app_info: AppInfo, target_app_project_dir: Path) -> AppInfo:
    pyproject_toml_file_name = "pyproject.toml"
    pyproject_toml_file_path = Path(target_app_project_dir, pyproject_toml_file_name)

    # info from pyproject.toml overrides everything else
    log.info(f"loading {pyproject_toml_file_path} ({pyproject_toml_file_path.absolute()})")
    if pyproject_toml_file_path.exists():
        with pyproject_toml_file_path.open() as f:
            pyproject = toml.load(f)
            project_section = pyproject.get("project")
            if project_section is not None:
                app_info.name = project_section.get("name")
                app_info.author = project_section.get("author")  # app author

            tool_section = pyproject.get("tool")
            if tool_section is not None:
                if app_info.name is None:
                    # The user didn't provide a separate [project].name so let's try to get it from what flit writes out at [tool.flit.metadata]/module.
                    # This is all we want or need to get from tool.flit.metadata since the remainder of the fields will be in the package distribution.
                    flit_section = tool_section.get("flit")
                    if flit_section is not None:
                        flit_metadata = flit_section.get("metadata")
                        if flit_metadata is not None:
                            app_info.name = flit_metadata.get("module")

                # get info from pyship section
                # [tool.pyship]
                pyship_app_info = tool_section.get("pyship")
                if pyship_app_info is not None:
                    app_info.is_gui = pyship_app_info.get("is_gui")  # False if CLI
                    app_info.run_on_startup = pyship_app_info.get("run_on_startup")
    return app_info


@typechecked
def get_app_info_wheel(app_info: AppInfo, dist_path: Path) -> AppInfo:
    if dist_path is not None and dist_path.exists():
        wheel_info = inspect_wheel(dist_path)
        metadata = wheel_info["dist_info"]["metadata"]
        app_info.name = metadata.get("name")
        app_info.version = VersionInfo.parse(metadata.get("version"))
        app_info.author = metadata.get("author")
        app_info.description = metadata.get("summary", "")  # called description in setup.py
    return app_info


@typechecked
def get_app_info(target_app_project_dir: Path, target_app_dist_dir: Path, cache_dir: Optional[Path] = None) -> AppInfo:
    """
    Get combined app info from all potential sources.
    :param target_app_project_dir: app project dir, e.g. where a pyproject.toml may reside. (optional)
    :param target_app_dist_dir: the "distribution" dir, e.g. where a wheel may reside (optional)
    :param cache_dir: cache dir for uv bootstrap (optional)
    :return: an AppInfo instance
    """

    app_info = AppInfo()
    app_info.setup_paths(target_app_project_dir)

    get_app_info_py_project(app_info, target_app_project_dir)

    if app_info.name is None:
        log.error(f"{app_info.name=} {target_app_project_dir=}")
    else:
        wheel_glob = f"{app_info.name}*.whl"
        wheel_list = list(target_app_dist_dir.glob(wheel_glob))
        if len(wheel_list) < 1:
            # No wheel file exists - build it using uv
            from pyship.uv_util import find_or_bootstrap_uv, uv_build

            if cache_dir is not None:
                uv_path = find_or_bootstrap_uv(cache_dir)
                uv_build(uv_path, target_app_project_dir, target_app_dist_dir)
                wheel_list = list(target_app_dist_dir.glob(wheel_glob))  # try again to find the wheel
            else:
                log.warning("no cache_dir provided, cannot bootstrap uv to build wheel")

        if len(wheel_list) == 0:
            log.error(f"{app_info.name} : no wheel at {target_app_dist_dir} ({target_app_dist_dir.absolute()})")
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
                    raise PyshipInsufficientAppInfo
                else:
                    pyship_print(f"{required_field}={attribute_value}")

            app_info.icon_file_name = f"{app_info.name}.ico"

    return app_info
