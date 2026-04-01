from pathlib import Path

from semver import VersionInfo

from pyship.launcher import calculate_metadata


def test_metadata_includes_ui(tmp_path):
    """Verify that calculate_metadata includes the ui field."""
    launcher_dir = tmp_path / "launcher"
    launcher_dir.mkdir()
    (launcher_dir / "launcher.py").write_text("# stub")
    icon_path = tmp_path / "icon.ico"
    icon_path.write_bytes(b"\x00\x00")

    metadata = calculate_metadata("myapp", "testauthor", VersionInfo.parse("1.0.0"), launcher_dir, icon_path, "tui")
    assert metadata["ui"] == "tui"
    assert "is_gui" not in metadata


def test_metadata_ui_cli(tmp_path):
    launcher_dir = tmp_path / "launcher"
    launcher_dir.mkdir()
    (launcher_dir / "launcher.py").write_text("# stub")
    icon_path = tmp_path / "icon.ico"
    icon_path.write_bytes(b"\x00\x00")

    metadata = calculate_metadata("myapp", "testauthor", VersionInfo.parse("2.0.0"), launcher_dir, icon_path, "cli")
    assert metadata["ui"] == "cli"


def test_metadata_ui_gui(tmp_path):
    launcher_dir = tmp_path / "launcher"
    launcher_dir.mkdir()
    (launcher_dir / "launcher.py").write_text("# stub")
    icon_path = tmp_path / "icon.ico"
    icon_path.write_bytes(b"\x00\x00")

    metadata = calculate_metadata("myapp", "testauthor", VersionInfo.parse("3.0.0"), launcher_dir, icon_path, "gui")
    assert metadata["ui"] == "gui"
