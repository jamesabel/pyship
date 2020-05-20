from pyship import ModuleInfo
from test_pyship import TST_APP_NAME, TST_APP_PROJECT_DIR


def test_module_info():
    module_info = ModuleInfo(TST_APP_NAME, TST_APP_PROJECT_DIR)
    print(module_info)
