from pathlib import Path

__application_name__ = "test_pyship"

from .tst_app import TST_APP_NAME, TstAppDirs

# todo: remove this when pyshipupdate is on PyPI
PYSHIP_DIST_DIR = Path("dist").absolute()
find_links = [PYSHIP_DIST_DIR, Path(Path.home(), "projects", "pyshipupdate", "dist")]
