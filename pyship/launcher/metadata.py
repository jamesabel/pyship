import json
from pathlib import Path

from typeguard import typechecked
from pyship.launcher import get_file_sha256


@typechecked(always=True)
def calculate_launcher_metadata(pyship_dir: Path, icon_file_path: Path) -> dict:
    launcher_metadata = {}
    file_paths = [p for p in Path(pyship_dir).glob("launch*.py")]
    file_paths.append(icon_file_path)
    for p in file_paths:
        launcher_metadata[f"{p.name}_sha256"] = get_file_sha256(p)
    return launcher_metadata


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
        launcher_metadata = json.dump(metadata, f, indent=4)
    return launcher_metadata
