from pathlib import Path

from pyship import create_pyshipy, TargetAppInfo
from test_pyship import TST_APP_DIR, TST_APP_DIST, TST_APP_CACHE


def test_build_pyshipy():
    target_app_info = TargetAppInfo(Path(TST_APP_DIR, "pyproject.toml"))
    create_pyshipy(target_app_info, TST_APP_DIST, TST_APP_CACHE, target_app_dir=TST_APP_DIR)
    target_pyship_python_path = Path(TST_APP_DIST)
    assert(target_pyship_python_path.exists())
