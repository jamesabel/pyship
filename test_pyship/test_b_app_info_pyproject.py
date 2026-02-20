from pathlib import Path

from semver import VersionInfo

from pyship import AppInfo, get_app_info_py_project


def _write_pyproject(tmp_path: Path, content: str) -> None:
    (tmp_path / "pyproject.toml").write_text(content, encoding="utf-8")


def test_pep621_name(tmp_path):
    _write_pyproject(tmp_path, '[project]\nname = "myapp"\nversion = "1.0.0"\n')
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.name == "myapp"


def test_pep621_version_parsed(tmp_path):
    _write_pyproject(tmp_path, '[project]\nname = "myapp"\nversion = "2.3.4"\n')
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.version == VersionInfo.parse("2.3.4")


def test_pep621_authors_list(tmp_path):
    _write_pyproject(
        tmp_path,
        '[project]\nname = "myapp"\nversion = "1.0.0"\n\n[[project.authors]]\nname = "Jane Doe"\nemail = "jane@example.com"\n',
    )
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.author == "Jane Doe"


def test_pep621_author_string_fallback(tmp_path):
    _write_pyproject(tmp_path, '[project]\nname = "myapp"\nversion = "1.0.0"\nauthor = "John Smith"\n')
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.author == "John Smith"


def test_tool_pyship_is_gui_true(tmp_path):
    _write_pyproject(
        tmp_path,
        '[project]\nname = "myapp"\nversion = "1.0.0"\n\n[tool.pyship]\nis_gui = true\n',
    )
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.is_gui is True


def test_tool_pyship_is_gui_false(tmp_path):
    _write_pyproject(
        tmp_path,
        '[project]\nname = "myapp"\nversion = "1.0.0"\n\n[tool.pyship]\nis_gui = false\n',
    )
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.is_gui is False


def test_tool_pyship_run_on_startup(tmp_path):
    _write_pyproject(
        tmp_path,
        '[project]\nname = "myapp"\nversion = "1.0.0"\n\n[tool.pyship]\nrun_on_startup = true\n',
    )
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.run_on_startup is True


def test_missing_pyproject_toml_returns_unchanged(tmp_path):
    # No pyproject.toml in tmp_path - all fields remain None
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.name is None
    assert app_info.version is None
    assert app_info.author is None


def test_does_not_mutate_original_app_info(tmp_path):
    _write_pyproject(tmp_path, '[project]\nname = "myapp"\nversion = "1.0.0"\n')
    original = AppInfo()
    result = get_app_info_py_project(original, tmp_path)
    # The function deep-copies - original should be unchanged
    assert original.name is None
    assert result.name == "myapp"


def test_flit_legacy_format(tmp_path):
    _write_pyproject(
        tmp_path,
        '[build-system]\nrequires = ["flit_core"]\n\n[tool.flit.metadata]\nmodule = "myflitapp"\nauthor = "abel"\n',
    )
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.name == "myflitapp"


def test_pep621_overrides_flit_name(tmp_path):
    """[project].name takes precedence over [tool.flit.metadata].module."""
    _write_pyproject(
        tmp_path,
        '[project]\nname = "pep621name"\nversion = "1.0.0"\n\n[tool.flit.metadata]\nmodule = "flitname"\n',
    )
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.name == "pep621name"


def test_empty_pyproject_toml(tmp_path):
    _write_pyproject(tmp_path, "")
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.name is None


def test_no_version_in_pyproject(tmp_path):
    _write_pyproject(tmp_path, '[project]\nname = "myapp"\n')
    app_info = get_app_info_py_project(AppInfo(), tmp_path)
    assert app_info.name == "myapp"
    assert app_info.version is None
