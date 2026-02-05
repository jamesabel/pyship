import json
from pathlib import Path
from typing import Union

from semver import VersionInfo

from pyship import __version__ as pyship_version
from pyship.launcher import get_file_sha256

from typeguard import typechecked


@typechecked
def calculate_metadata(target_app_name: str, target_app_author: str, target_app_version: VersionInfo, launcher_source_dir: Path, icon_path: Path, is_gui: bool) -> dict:
    launcher_metadata = {
        "app": target_app_name,
        "version": str(target_app_version),
        "author": target_app_author,
        "pyship_version": pyship_version,
        "icon_sha256": get_file_sha256(icon_path),
        "is_gui": is_gui,
    }
    # Hash launcher Python sources
    for p in launcher_source_dir.glob("*.py"):
        launcher_metadata[f"{p.name}_sha256"] = get_file_sha256(p)
    # Hash the C# stub template (in the parent pyship package)
    launcher_stub_path = launcher_source_dir.parent / "launcher_stub.py"
    if launcher_stub_path.exists():
        launcher_metadata["launcher_stub.py_sha256"] = get_file_sha256(launcher_stub_path)
    return launcher_metadata


@typechecked
def get_metadata_file_path(launcher_dir: Path, launcher_filename: str) -> Path:
    return Path(launcher_dir, launcher_filename)


@typechecked
def load_metadata(launcher_dir: Path, launcher_filename: str) -> Union[dict, None]:
    launcher_metadata_file_path = get_metadata_file_path(launcher_dir, launcher_filename)
    if launcher_metadata_file_path.exists():
        with launcher_metadata_file_path.open() as f:
            launcher_metadata = json.load(f)
    else:
        launcher_metadata = None
    return launcher_metadata


@typechecked
def store_metadata(launcher_dir: Path, launcher_filename: str, metadata: dict):
    launcher_dir.mkdir(exist_ok=True)
    with get_metadata_file_path(launcher_dir, launcher_filename).open("w") as f:
        json.dump(metadata, f, indent=4)
