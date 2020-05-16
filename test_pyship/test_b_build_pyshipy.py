from pathlib import Path

from pyship import create_pyshipy, TargetAppInfo


def test_build_pyshipy():
    temp_dir = Path("temp", "test")
    temp_dir.mkdir(parents=True, exist_ok=True)
    target_app_info = TargetAppInfo(Path("test_pyship", "tstpyshipapp", "pyproject.toml"))
    create_pyshipy(target_app_info, Path(temp_dir, "dist"), Path(temp_dir, "cache"))
