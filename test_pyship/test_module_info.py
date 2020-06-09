from semver import VersionInfo

from pyship import ModuleInfo

from test_pyship import TstAppDirs, TST_APP_NAME


def test_module_info():
    for version_string in ["0.0.1", "0.0.2"]:
        version = VersionInfo.parse(version_string)
        tst_app_dirs = TstAppDirs(TST_APP_NAME, version)
        module_info = ModuleInfo(TST_APP_NAME, tst_app_dirs.project_dir)
        print(module_info.version)
        assert module_info.version == version
