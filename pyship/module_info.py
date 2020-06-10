import sys
from importlib import import_module, reload, invalidate_caches
from dataclasses import dataclass
from pathlib import Path

from semver import VersionInfo

from pyship import __application_name__, get_logger, pyship_print

log = get_logger(__application_name__)


@dataclass
class ModuleInfo:

    """
    get module info (name, version, docstring, etc.)
    """

    def __init__(self, name: str, path: Path = None):

        self.name = name
        self.path = path
        self.version = None
        self.docstring = ""

        # only temporarily put this module in the path if it's not there already
        if appended_path := self.path is not None and str(self.path) not in sys.path:
            sys.path.append(str(self.path))

        try:

            # Do as much as we can to ensure we can import a module already imported, since we re-load the test app module in our test cases (probably not something we'll see in normal
            # usage though).
            invalidate_caches()
            app_module = import_module(self.name)
            app_module = reload(app_module)  # for our test cases we need to reload a modified module (it doesn't hurt to reload an unmodified module)
            version_string = app_module.__dict__.get("__version__")
            pyship_print(f"{self.name=} {version_string=}")

            if version_string is None:
                log.error(f"{self.name} does not have a __version__.  Please add one.")
            else:
                self.version = VersionInfo.parse(version_string)

            self.docstring = app_module.__dict__.get("__doc__")
            if self.docstring is None:
                log.warning(f"{self.name} does not have a docstring.  Please add one.")
            else:
                self.docstring = self.docstring.strip()

        except ModuleNotFoundError:
            log.info(f"{sys.path=}")
            log.error(f"Your module {self.name} was not found in your python environment.  Perhaps it is not installed.  Check if {self.name} is in sys.path.")

        if appended_path:
            sys.path.remove(str(self.path))
