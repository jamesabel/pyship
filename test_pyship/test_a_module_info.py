from pyship import ModuleInfo
from test_pyship import TST_APP_NAME_0_0_1, TST_APP_PROJECT_DIR


def test_module_info():
    module_info = ModuleInfo(TST_APP_NAME_0_0_1, TST_APP_PROJECT_DIR)
    print(module_info)
