from semver import VersionInfo

from pyship import UpdaterLocal

from test_pyship import TST_APP_NAME, TstAppDirs


def test_find_latest_version():
    # this requires update to already have been run
    version_strings = ["0.0.1", "0.0.2"]
    updater_local = UpdaterLocal(TST_APP_NAME)
    updater_local.packaged_app_dirs = set([TstAppDirs(TST_APP_NAME, VersionInfo.parse(vs)).dist_dir for vs in version_strings])
    available_versions = updater_local.get_available_versions()
    assert len(available_versions) == 2
    greatest_version = updater_local.get_greatest_version(available_versions)
    assert greatest_version == VersionInfo.parse(version_strings[-1])
