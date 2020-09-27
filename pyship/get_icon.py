from typing import Tuple, Callable
from pathlib import Path
import shutil

from typeguard import typechecked

from pyship import AppInfo, get_logger, __application_name__
import pyship

log = get_logger(__application_name__)


@typechecked()
def get_icon(target_app_info: AppInfo, ui_print: Callable) -> Path:
    """
    find either the target project's icon or the provided icon from pyship
    :param target_app_info: target app info
    :param ui_print: this function is called with a string to update the UI
    :return: icon's path
    """

    icon_file_name = f"{target_app_info.name}.ico"
    icon_path = Path(target_app_info.project_dir, icon_file_name).absolute()  # default
    alternate_icon_path = Path(target_app_info.project_dir, target_app_info.name, icon_file_name).absolute()

    if not icon_path.exists() and alternate_icon_path.exists():
        icon_path = alternate_icon_path

    if not icon_path.exists():

        # use pyship's icon if the target app doesn't have one
        pyship_icon_path = Path(Path(pyship.__file__).parent, f"{__application_name__}.ico").absolute()
        s = f"{target_app_info.name} does not include its own icon - using {__application_name__} icon ({pyship_icon_path})"
        log.info(s)
        ui_print(s)
        if pyship_icon_path.exists():
            log.info(f"copying {pyship_icon_path} to {icon_path}")
            shutil.copy2(pyship_icon_path, icon_path)
        else:
            log.fatal(f"{pyship_icon_path} does not exist")

    return icon_path
