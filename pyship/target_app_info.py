from pathlib import Path

import toml

from pyship import __application_name__ as pyship_application_name, get_logger, ModuleInfo

log = get_logger(pyship_application_name)


class TargetAppInfo:
    """
    get target app info
    """

    def __init__(self, target_app_dir: Path = Path()):
        """
        get target app info
        :param target_app_dir: path to target module package (directory with a __init__.py) or None to use the current directory
        """

        pyproject_toml_file_name = "pyproject.toml"

        self.name = None
        self.author = None
        self.is_gui = False
        self.url = ""
        self.description = ""
        self.run_on_startup = False
        self.target_app_dir = target_app_dir
        self.pyproject_toml_file_path = Path(self.target_app_dir, pyproject_toml_file_name)

        log.info(f"loading {self.pyproject_toml_file_path} ({self.pyproject_toml_file_path.absolute()})")
        if self.pyproject_toml_file_path.exists():

            with self.pyproject_toml_file_path.open() as f:
                pyproject = toml.load(f)
                project_section = pyproject.get("project")
                if project_section is None:
                    log.error(f"no [project] table in {self.pyproject_toml_file_path}")
                else:
                    self.name = project_section.get("name")  # app name
                    self.author = project_section.get("author")  # app author

                    if self.name is None:
                        log.error(f"project name not in [project] table in {self.pyproject_toml_file_path}")
                    elif self.author is None:
                        log.error(f"project author not in [project] table in {self.pyproject_toml_file_path}")
                    else:

                        tool_section = pyproject.get("tool")
                        if tool_section:

                            # get info from pyship section
                            # [tool.pyship]
                            pyship_app_info = tool_section.get("pyship")
                            if pyship_app_info is None:
                                log.error(f"no pyship table in {self.pyproject_toml_file_path}")
                            else:
                                self.is_gui = pyship_app_info.get("is_gui", self.is_gui)  # False if CLI
                                self.run_on_startup = pyship_app_info.get("run_on_startup", self.run_on_startup)

                            # get info from flit section
                            # [tool.flit.metadata]
                            flit_tool = tool_section.get("flit")
                            if flit_tool is not None:
                                flit_metadata = flit_tool.get("metadata")
                                if flit_metadata is not None:
                                    self.url = flit_metadata.get("home-page")

                        module_info = ModuleInfo(self.name, Path(self.pyproject_toml_file_path.parent, self.name))
                        self.version = module_info.version
                        self.description = module_info.docstring

        else:
            log.error(f"{str(self.pyproject_toml_file_path)} does not exist at {self.pyproject_toml_file_path.absolute().parent}")

    def is_complete(self):
        return self.name is not None and self.author is not None
