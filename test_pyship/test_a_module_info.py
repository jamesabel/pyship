from semver import VersionInfo

from pyship import ModuleInfo
from test_pyship import TST_APP_NAME, TstAppDirs


def test_module_info():
    tst_app_dirs = TstAppDirs(TST_APP_NAME, VersionInfo.parse("0.0.1"))
    module_info = ModuleInfo(TST_APP_NAME, tst_app_dirs.project_dir)
    print(module_info)
