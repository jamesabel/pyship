from semver import VersionInfo

from pyship import UpdaterLocal
from test_pyship import TstAppDirs, TST_APP_NAME


def test_update_local():
    """
    Test only the updater (without calling PyShip.ship() ) on the local system.  Helpful in debugging the updater, since ship() takes a lot of time.
    """

    # todo: put this into a function since this is shared with test_find_latest_version()
    versions = [VersionInfo.parse(vs) for vs in ["0.0.1", "0.0.2"]]
    updater_local = UpdaterLocal(TST_APP_NAME)
    updater_local.app_dirs = set([TstAppDirs(TST_APP_NAME, v).app_dir for v in versions])
    did_update = updater_local.update(versions[0], TstAppDirs(TST_APP_NAME, versions[0]).app_dir)
    assert did_update
