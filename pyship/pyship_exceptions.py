from pathlib import Path
from typing import Tuple


class PyshipException(Exception):
    pass


class PyshipNoProductDirectory(PyshipException):
    def __init__(self, path: Path):
        super().__init__(self.__class__.__name__, str(path))


class PyshipCouldNotGetVersion(PyshipException):
    def __init__(self, python_ver_tuple: Tuple):
        super().__init__(self.__class__.__name__, python_ver_tuple)


class PyshipLicenseFileDoesNotExist(PyshipException):
    def __init__(self, path: Path):
        super().__init__(self.__class__.__name__, path)


class PyshipInsufficientAppInfo(PyshipException):
    def __init__(self):
        super().__init__(self.__class__.__name__)
