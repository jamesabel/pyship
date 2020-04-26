from attr import attrs, attrib
from pathlib import Path

import toml
from balsa import get_logger

from pyship import __application_name__ as pyship_application_name

log = get_logger(pyship_application_name)


@attrs()
class TargetAppInfo:
    name = attrib(default=None)
    is_gui = attrib(default=False)
    pyproject_toml_file_path = attrib(default=Path("pyproject.toml"))

    def __attrs_post_init__(self):
        self.get_pyproject_info()

    def get_pyproject_info(self):
        log.info(f"loading {self.pyproject_toml_file_path}")
        if self.pyproject_toml_file_path.exists():
            with open(self.pyproject_toml_file_path) as f:
                pyproject = toml.load(f)
                tool_section = pyproject.get("tool")
                if tool_section:
                    pyship_section = tool_section.get(pyship_application_name)
                    self.name = pyship_section.get("app")
                    self.is_gui = pyship_section.get("is_gui", self.is_gui)
        else:
            log.error(f"{str(self.pyproject_toml_file_path)} does not exist")

    def is_complete(self):
        return self.name is not None
