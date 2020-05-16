from pyship import TargetAppInfo
from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author


def test_pyproject():
    target_app_info = TargetAppInfo()
    assert(target_app_info.name == pyship_application_name)
    assert(target_app_info.author == pyship_author)
    assert(target_app_info.is_gui is not None)
