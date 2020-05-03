import json
from pathlib import Path

from pyship import __version__ as pyship_version
from pyship.launcher import get_file_sha256

from typeguard import typechecked


@typechecked(always=True)
def calculate_launcher_metadata(target_app_name: str, target_app_author: str, launcher_source_dir: Path, icon_path: Path, is_gui: bool) -> dict:
    launcher_metadata = {"app": target_app_name,
                         "author": target_app_author,
                         "pyship_version": pyship_version,
                         "icon_sha256": get_file_sha256(icon_path),
                         "is_gui": is_gui}
    for p in launcher_source_dir.glob("*.py"):
        launcher_metadata[f"{p.name}_sha256"] = get_file_sha256(p)
    return launcher_metadata


@typechecked(always=True)
def get_launcher_metadata_file_path(launcher_dir: Path, launcher_filename: str) -> Path:
    return Path(launcher_dir, launcher_filename)


@typechecked(always=True)
def load_launcher_metadata(launcher_dir: Path, launcher_filename: str) -> (dict, None):
    launcher_metadata_file_path = get_launcher_metadata_file_path(launcher_dir, launcher_filename)
    if launcher_metadata_file_path.exists():
        with launcher_metadata_file_path.open() as f:
            launcher_metadata = json.load(f)
    else:
        launcher_metadata = None
    return launcher_metadata


@typechecked(always=True)
def store_launcher_metadata(launcher_dir: Path, launcher_filename: str, metadata: dict):
    launcher_dir.mkdir(exist_ok=True)
    with get_launcher_metadata_file_path(launcher_dir, launcher_filename).open('w') as f:
        json.dump(metadata, f, indent=4)
