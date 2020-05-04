from pathlib import Path

import toml

from pyship import __application_name__ as pyship_application_name, get_logger

log = get_logger(pyship_application_name)


class TargetAppInfo:

    def __init__(self, pyproject_toml_file_path: Path = Path("pyproject.toml")):

        self.name = None
        self.author = None
        self.is_gui = False
        self.url = ""
        self.description = ""
        self.run_on_startup = False

        self.pyproject_toml_file_path = pyproject_toml_file_path
        log.info(f"loading {self.pyproject_toml_file_path}")
        if self.pyproject_toml_file_path.exists():
            with self.pyproject_toml_file_path.open() as f:
                pyproject = toml.load(f)
                tool_section = pyproject.get("tool")
                if tool_section:

                    # get info from flit section
                    # [tool.flit.metadata]
                    flit_metadata = tool_section.get("flit").get("metadata")
                    self.name = flit_metadata.get("module")  # app name
                    self.author = flit_metadata.get("author")  # app author
                    self.url = flit_metadata.get("home-page")

                    # get info from pyship section
                    # [tool.pyship]
                    pyship_app_info = tool_section.get("pyship")
                    self.description = pyship_app_info.get("description", self.description)
                    self.is_gui = pyship_app_info.get("is_gui", self.is_gui)  # False if CLI
                    self.run_on_startup = pyship_app_info.get("run_on_startup", self.run_on_startup)

        else:
            log.error(f"{str(self.pyproject_toml_file_path)} does not exist at {self.pyproject_toml_file_path.absolute().parent}")

    def is_complete(self):
        return self.name is not None and self.author is not None
