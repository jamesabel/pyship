"""
Shared installer naming.

Both installer types pyship produces - the NSIS installer (``.exe``) and the
MSIX package (``.msix``) - are written to the ``installers/`` directory in the
target project and follow the same ``{app_name}_installer_{target_os}.{ext}``
naming convention (``target_os`` is e.g. ``win64``). This module is the single
source of truth for that convention.
"""

from pathlib import Path

from typeguard import typechecked

from pyshipupdate import get_target_os

#: Name of the directory (inside the target project dir) that receives installers.
INSTALLERS_DIR_NAME = "installers"


@typechecked
def installer_file_name(app_name: str, extension: str) -> str:
    """
    Return the canonical installer file name for an app.

    :param app_name: target application name
    :param extension: installer file extension without the dot, e.g. ``"exe"`` or ``"msix"``
    :return: file name such as ``"myapp_installer_win64.exe"``
    """
    return f"{app_name}_installer_{get_target_os()}.{extension}"


@typechecked
def get_installers_dir(project_dir: Path) -> Path:
    """
    Return the installers output directory for a target project.

    :param project_dir: target application project directory
    :return: path to the project's ``installers/`` directory (not created)
    """
    return Path(project_dir, INSTALLERS_DIR_NAME)
