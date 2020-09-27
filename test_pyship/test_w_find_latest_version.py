from semver import VersionInfo

from pyship.updater import UpdaterLocal

from test_pyship import TST_APP_NAME, TstAppDirs


def test_find_latest_version():
    """
    Find the latest version.  Helpful in debugging the finder, since ship() takes a lot of time.
    """
    # this requires update to already have been run
    version_strings = ["0.0.1", "0.0.2"]
    updater_local = UpdaterLocal(TST_APP_NAME)
    updater_local.app_dirs = set([TstAppDirs(TST_APP_NAME, VersionInfo.parse(vs)).app_dir for vs in version_strings])
    available_versions = updater_local.get_available_versions()
    assert len(available_versions) == 2
    greatest_version = updater_local.get_greatest_version()
    assert greatest_version == VersionInfo.parse(version_strings[-1])
