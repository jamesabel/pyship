from pathlib import Path

import pyship
from pyship import AppInfo, get_icon


def _make_app_info(project_dir: Path, name: str = "testapp") -> AppInfo:
    app_info = AppInfo()
    app_info.name = name
    app_info.project_dir = project_dir
    return app_info


def test_get_icon_fallback_to_pyship_icon(tmp_path):
    """With no app icon present, falls back to pyship's own .ico."""
    app_info = _make_app_info(tmp_path)
    icon_path = get_icon(app_info, lambda s: None)
    expected = Path(Path(pyship.__file__).parent, "pyship.ico").absolute()
    assert icon_path == expected


def test_get_icon_uses_project_root_icon(tmp_path):
    """App icon in the project root directory is used first."""
    app_info = _make_app_info(tmp_path)
    icon_file = tmp_path / "testapp.ico"
    icon_file.write_bytes(b"\x00" * 4)  # minimal fake ICO
    icon_path = get_icon(app_info, lambda s: None)
    assert icon_path == icon_file.absolute()


def test_get_icon_uses_app_subdir_icon(tmp_path):
    """App icon in <project_dir>/<app_name>/ is found."""
    app_info = _make_app_info(tmp_path)
    subdir = tmp_path / "testapp"
    subdir.mkdir()
    icon_file = subdir / "testapp.ico"
    icon_file.write_bytes(b"\x00" * 4)
    icon_path = get_icon(app_info, lambda s: None)
    assert icon_path == icon_file.absolute()


def test_get_icon_uses_icon_subdir(tmp_path):
    """App icon in <project_dir>/icon/ is found."""
    app_info = _make_app_info(tmp_path)
    icon_dir = tmp_path / "icon"
    icon_dir.mkdir()
    icon_file = icon_dir / "testapp.ico"
    icon_file.write_bytes(b"\x00" * 4)
    icon_path = get_icon(app_info, lambda s: None)
    # This is priority 5 in the list; root is priority 1, so only reachable
    # if none of the higher-priority paths exist (which they don't in tmp_path)
    assert icon_path == icon_file.absolute()


def test_get_icon_returns_existing_path(tmp_path):
    """The returned icon path always points to an existing file."""
    app_info = _make_app_info(tmp_path)
    icon_path = get_icon(app_info, lambda s: None)
    assert icon_path.exists()


def test_get_icon_calls_ui_print(tmp_path):
    """ui_print callback is called at least once."""
    app_info = _make_app_info(tmp_path)
    messages = []
    get_icon(app_info, messages.append)
    assert len(messages) >= 1
    assert all(isinstance(m, str) for m in messages)


def test_get_icon_ui_print_receives_string_with_path(tmp_path):
    """ui_print message mentions the icon path."""
    app_info = _make_app_info(tmp_path)
    messages = []
    get_icon(app_info, messages.append)
    # At least one message should contain the word "icon" or the file name
    combined = " ".join(messages).lower()
    assert "icon" in combined or "pyship" in combined


def test_get_icon_name_used_in_icon_filename(tmp_path):
    """The icon file name is based on the app name."""
    app_name = "specialapp"
    app_info = _make_app_info(tmp_path, name=app_name)
    # Place icon at root with app name
    icon_file = tmp_path / f"{app_name}.ico"
    icon_file.write_bytes(b"\x00" * 4)
    icon_path = get_icon(app_info, lambda s: None)
    assert icon_path.name == f"{app_name}.ico"
