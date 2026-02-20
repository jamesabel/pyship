from pathlib import Path

from .make_test_app import make_test_app


def test_make_test_app():

    test_name = "test_make_test_app"
    app_name = "tstpyshipapp"
    app_version = "0.0.1"
    app_dir = Path("temp", test_name)
    make_test_app(app_dir, app_name, app_version, "3.13", False)
