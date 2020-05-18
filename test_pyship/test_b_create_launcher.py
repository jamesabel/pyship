from pathlib import Path
import os

from pyship import create_launcher, TargetAppInfo, mkdirs
from test_pyship import TST_APP_ROOT_DIR, TST_APP_SHIP_DIR, TST_APP_NAME, TST_APP_EXE_PATH


def test_create_launcher():

    target_app_info = TargetAppInfo(Path(TST_APP_ROOT_DIR, "pyproject.toml"))
    test_app_icon_path = Path(TST_APP_ROOT_DIR, f"{TST_APP_NAME}.ico")

    try:
        # first time with no user provided icon
        os.unlink(test_app_icon_path)
    except FileNotFoundError:
        pass

    for _ in range(0, 2):
        mkdirs(TST_APP_SHIP_DIR, remove_first=True)
        create_launcher(target_app_info, TST_APP_SHIP_DIR)
        assert(TST_APP_EXE_PATH.exists())

    os.unlink(test_app_icon_path)
