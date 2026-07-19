"""
pyship exception hierarchy. All pyship exceptions derive from :class:`PyshipException`.
"""

from pathlib import Path
from typing import Tuple


class PyshipException(Exception):
    """Base class for all pyship exceptions."""

    pass


class PyshipNoProductDirectory(PyshipException):
    """The expected product directory does not exist."""

    def __init__(self, path: Path):
        super().__init__(self.__class__.__name__, str(path))


class PyshipCouldNotGetVersion(PyshipException):
    """A usable version could not be determined."""

    def __init__(self, python_ver_tuple: Tuple):
        super().__init__(self.__class__.__name__, python_ver_tuple)


class PyshipNoAppName(PyshipException):
    """The target application name could not be determined (e.g. missing from pyproject.toml)."""

    def __init__(self):
        super().__init__(self.__class__.__name__)


class PyshipNoTargetAppInfo(PyshipException):
    """No target application info could be gathered."""

    def __init__(self):
        super().__init__(self.__class__.__name__)


class PyshipLicenseFileDoesNotExist(PyshipException):
    """The target project has no LICENSE file (required for the NSIS installer's license page)."""

    def __init__(self, path: Path):
        super().__init__(self.__class__.__name__, path)


class PyshipInsufficientAppInfo(PyshipException):
    """Required app info fields (name, author, version) are missing or invalid."""

    def __init__(self):
        super().__init__(self.__class__.__name__)


class PyshipSigningUnavailable(PyshipException):
    """code_sign is enabled but signing infrastructure is missing or a file failed to sign."""

    def __init__(self, message: str = ""):
        super().__init__(self.__class__.__name__, message)
