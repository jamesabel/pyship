from pathlib import Path
import os

from pyship import create_launcher, TargetAppInfo, mkdirs
from test_pyship import TST_APP_DIR, TST_APP_DIST, TST_APP_NAME


def test_create_launcher():

    target_app_info = TargetAppInfo(Path(TST_APP_DIR, "pyproject.toml"))
    launcher_exe_path = Path(TST_APP_DIST, f"{TST_APP_NAME}.exe")  # windows
    test_app_icon_path = Path(TST_APP_DIR, f"{TST_APP_NAME}.ico")

    try:
        # first time with no user provided icon
        os.unlink(test_app_icon_path)
    except FileNotFoundError:
        pass

    for _ in range(0, 2):
        mkdirs(TST_APP_DIST, remove_first=True)
        create_launcher(target_app_info, TST_APP_DIST)
        assert(launcher_exe_path.exists())

    os.unlink(test_app_icon_path)
