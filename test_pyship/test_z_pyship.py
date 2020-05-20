from pyship import PyShip
from test_pyship import TST_APP_PROJECT_DIR


def test_pyship():
    py_ship = PyShip(target_app_parent_dir=TST_APP_PROJECT_DIR)
    py_ship.ship()
