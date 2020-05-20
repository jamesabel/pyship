from pyship import ModuleInfo
from test_pyship import TST_APP_NAME, TST_APP_ROOT_DIR


def test_module_info():
    module_info = ModuleInfo(TST_APP_NAME, TST_APP_ROOT_DIR)
    print(module_info)
