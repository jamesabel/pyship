from pathlib import Path

import toml

from pyship import __application_name__ as pyship_application_name, get_logger

log = get_logger(pyship_application_name)


class TargetAppInfo:

    def __init__(self, pyproject_toml_file_path: Path = Path("pyproject.toml")):

        self.name = None
        self.author = None
        self.is_gui = False

        self.pyproject_toml_file_path = pyproject_toml_file_path
        log.info(f"loading {self.pyproject_toml_file_path}")
        if self.pyproject_toml_file_path.exists():
            with self.pyproject_toml_file_path.open() as f:
                pyproject = toml.load(f)
                tool_section = pyproject.get("tool")
                if tool_section:
                    pyship_section = tool_section.get(pyship_application_name)
                    self.name = pyship_section.get("app")  # app name
                    self.author = pyship_section.get("author")  # app author
                    self.is_gui = pyship_section.get("is_gui", self.is_gui)  # False if CLI
        else:
            log.error(f"{str(self.pyproject_toml_file_path)} does not exist at {self.pyproject_toml_file_path.absolute().parent}")

    def is_complete(self):
        return self.name is not None and self.author is not None
