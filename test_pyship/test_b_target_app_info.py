from pathlib import Path
from semver import parse

from pyship import TargetAppInfo
from pyship import __author__ as pyship_author
from test_pyship import TST_APP_ROOT_DIR, TST_APP_NAME


def test_pyproject():
    target_app_info = TargetAppInfo(Path(TST_APP_ROOT_DIR, "pyproject.toml"))
    assert(target_app_info.name == TST_APP_NAME)
    assert(target_app_info.author == pyship_author)
    assert(target_app_info.is_gui is not None)
    assert(target_app_info.target_app_dir.exists())
    assert(target_app_info.description is not None)
    assert(len(target_app_info.description) > 1)
    assert(target_app_info.version is not None)
    assert(target_app_info.version > parse("0.0.0"))
