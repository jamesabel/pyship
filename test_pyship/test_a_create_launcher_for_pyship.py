from pathlib import Path

from ismain import is_main

from pyshipupdate import rmdir
from pyship import create_launcher, AppInfo, __application_name__, __author__, __version__


def test_a_create_launcher_for_pyship():

    project_dir = Path().absolute()
    print(f"{project_dir=}")

    # subprocess.run("local_install.bat", cwd=project_dir)

    # create a launcher for pyship itself
    target_app_info = AppInfo(__application_name__, __author__, __version__, False, project_dir=project_dir)
    app_path = Path("app")
    rmdir(app_path)  # for the full app, this is done in the overall pyship infrastructure
    create_launcher(target_app_info, app_path)


if is_main():
    test_a_create_launcher_for_pyship()
