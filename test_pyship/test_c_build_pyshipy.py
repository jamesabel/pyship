from pathlib import Path

from pyship import create_pyshipy, TargetAppInfo
from test_pyship import TST_APP_ROOT_DIR, TST_APP_FROZEN_DIR, TST_APP_CACHE


def test_build_pyshipy():
    target_app_info = TargetAppInfo(Path(TST_APP_ROOT_DIR, "pyproject.toml"))
    create_pyshipy(target_app_info, TST_APP_FROZEN_DIR, TST_APP_CACHE, target_app_source_dir=TST_APP_ROOT_DIR)
    target_pyship_python_path = Path(TST_APP_FROZEN_DIR)
    assert(target_pyship_python_path.exists())
