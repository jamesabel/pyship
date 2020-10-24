from pathlib import Path

from pyship import get_app_info_py_project, AppInfo


def test_flit_pyproject_toml():
    app_info = AppInfo()
    updated_app_info = get_app_info_py_project(app_info, Path("test_pyship", "data", "flit_pyproject_toml"))
    assert updated_app_info.name == "pyshipexample"
