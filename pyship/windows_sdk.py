"""
Windows SDK command-line tool discovery.

The Windows SDK installs versioned tool directories under
``C:\\Program Files (x86)\\Windows Kits\\10\\bin`` (e.g. ``10.0.22621.0``).
:func:`find_sdk_tool` locates a tool (signtool.exe, makeappx.exe, ...) from the
highest installed SDK version, and is shared by the code-signing and MSIX modules.
"""

from pathlib import Path
from typing import Union

from typeguard import typechecked

#: Default Windows SDK bin directory searched by :func:`find_sdk_tool`.
WINDOWS_SDK_BIN_DIR = Path(r"C:\Program Files (x86)\Windows Kits\10\bin")


@typechecked
def find_sdk_tool(tool_name: str, sdk_bin_dir: Path = WINDOWS_SDK_BIN_DIR) -> Union[Path, None]:
    """
    Locate a Windows SDK tool executable.

    Scans versioned subdirectories of *sdk_bin_dir* (e.g. ``10.0.22621.0``) and
    returns the ``x64/<tool_name>`` from the highest SDK version that contains it.

    :param tool_name: executable file name, e.g. ``"signtool.exe"`` or ``"makeappx.exe"``
    :param sdk_bin_dir: Windows SDK bin directory to search
    :return: path to the tool from the highest SDK version, or None if not found
    """
    if not sdk_bin_dir.is_dir():
        return None

    candidates = []
    for child in sdk_bin_dir.iterdir():
        if child.is_dir() and child.name.startswith("10."):
            tool_path = Path(child, "x64", tool_name)
            if tool_path.exists():
                try:
                    version_tuple = tuple(int(x) for x in child.name.split("."))
                    candidates.append((version_tuple, tool_path))
                except ValueError:
                    pass

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]
