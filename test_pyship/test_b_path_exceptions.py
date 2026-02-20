from pathlib import Path

import pytest

from pyship.path import NullPath
from pyship.exceptions import (
    PyshipException,
    PyshipNoProductDirectory,
    PyshipCouldNotGetVersion,
    PyshipNoAppName,
    PyshipNoTargetAppInfo,
    PyshipLicenseFileDoesNotExist,
    PyshipInsufficientAppInfo,
)


def test_null_path_is_path():
    assert isinstance(NullPath(), Path)


def test_null_path_is_null_path():
    assert isinstance(NullPath(), NullPath)


def test_null_path_default_string():
    # Default Path() on Windows resolves to ".", consistent with Path()
    assert str(NullPath()) == str(Path())


def test_null_path_not_equal_to_real_path():
    assert NullPath() != Path("/some/real/path")


def test_pyship_exception_is_exception():
    with pytest.raises(PyshipException):
        raise PyshipException("test error")


def test_pyship_exception_is_base_for_all():
    subclasses = [
        PyshipNoProductDirectory(Path("/p")),
        PyshipCouldNotGetVersion((3, 11)),
        PyshipNoAppName(),
        PyshipNoTargetAppInfo(),
        PyshipLicenseFileDoesNotExist(Path("/p")),
        PyshipInsufficientAppInfo(),
    ]
    for exc in subclasses:
        assert isinstance(exc, PyshipException)


def test_pyship_no_product_directory_includes_path():
    path = Path("/some/missing/dir")
    exc = PyshipNoProductDirectory(path)
    assert any(str(path) in str(a) for a in exc.args)


def test_pyship_could_not_get_version_includes_tuple():
    ver = (3, 11)
    exc = PyshipCouldNotGetVersion(ver)
    assert ver in exc.args


def test_pyship_no_app_name_class_name_in_args():
    exc = PyshipNoAppName()
    assert "PyshipNoAppName" in exc.args[0]


def test_pyship_no_target_app_info_class_name_in_args():
    exc = PyshipNoTargetAppInfo()
    assert "PyshipNoTargetAppInfo" in exc.args[0]


def test_pyship_license_file_does_not_exist_includes_path():
    path = Path("/missing/LICENSE")
    exc = PyshipLicenseFileDoesNotExist(path)
    assert path in exc.args


def test_pyship_insufficient_app_info_class_name_in_args():
    exc = PyshipInsufficientAppInfo()
    assert "PyshipInsufficientAppInfo" in exc.args[0]


def test_all_exceptions_catchable_as_pyship_exception():
    cases = [
        (PyshipNoProductDirectory, (Path("/p"),)),
        (PyshipCouldNotGetVersion, ((3, 11),)),
        (PyshipNoAppName, ()),
        (PyshipNoTargetAppInfo, ()),
        (PyshipLicenseFileDoesNotExist, (Path("/p"),)),
        (PyshipInsufficientAppInfo, ()),
    ]
    for exc_class, args in cases:
        with pytest.raises(PyshipException):
            raise exc_class(*args)
