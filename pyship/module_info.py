import sys
from importlib import import_module

from attr import attrs, attrib
from semver import VersionInfo

from pyship import __application_name__, get_logger

log = get_logger(__application_name__)


@attrs()
class ModuleInfo:
    name = attrib()
    path = attrib(default=None)
    version = attrib(default=None)
    docstring = attrib(default="")

    def __attrs_post_init__(self):

        if self.path is not None:
            if self.path not in sys.path:
                sys.path.append(str(self.path))

        try:
            app_module = import_module(self.name)

            version_string = app_module.__dict__.get("__version__")
            if version_string is None:
                log.error(f"your module {self.name} does not have a version attribute.  Please add one.")
            else:
                self.version = VersionInfo.parse(version_string)

            self.docstring = app_module.__dict__.get("__doc__")
            if self.docstring is None:
                log.warning(f"your module {self.name} does not have a docstring.  Please add one.")
            else:
                self.docstring = self.docstring.strip()

        except ModuleNotFoundError:
            log.info(f"{sys.path=}")
            log.error(f"your module {self.name} not found in your python environment.  Perhaps it is not installed.  Check if {self.name} is in sys.path.")