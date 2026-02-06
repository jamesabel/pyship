from pathlib import Path
import os
from semver import VersionInfo

from ismain import is_main

from pyshipupdate import mkdirs
from pyship import create_pyship_launcher, AppInfo, __author__
from test_pyship import TST_APP_NAME, TstAppDirs


def test_create_launcher():
    # create launcher for a target app

    version = VersionInfo.parse("0.0.1")
    tst_app_dirs = TstAppDirs(TST_APP_NAME, version)

    target_app_info = AppInfo(TST_APP_NAME, __author__, version, False, project_dir=tst_app_dirs.project_dir)
    test_app_icon_path = Path(tst_app_dirs.project_dir, f"{TST_APP_NAME}.ico")

    try:
        # first time with no user provided icon - will exit with the icon put back
        os.unlink(test_app_icon_path)
    except FileNotFoundError:
        pass

    for _ in range(0, 2):
        mkdirs(tst_app_dirs.app_dir, remove_first=True)
        create_pyship_launcher(target_app_info, tst_app_dirs.app_dir)
        assert tst_app_dirs.launcher_exe_path.exists()
        launcher_bat_path = tst_app_dirs.launcher_exe_path.with_suffix(".bat")
        assert launcher_bat_path.exists(), f"diagnostic .bat not found: {launcher_bat_path}"


if is_main():
    test_create_launcher()
