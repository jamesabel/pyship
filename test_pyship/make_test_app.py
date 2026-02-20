from pathlib import Path

import shutil
from semver import VersionInfo

from pyship import __author__

app_code_updater = """
import json
import sys

from pyshipupdate import UpdaterAwsS3, restart_return_code, ok_return_code
from pyshipupdate import __version__ as pyshipupdate_version

from .__init__ import __application_name__, __version__, __author__

def app():

    updater = UpdaterAwsS3(__application_name__, __author__)
    if updater.update(__version__):
        exit_code = restart_return_code  # app has been updated so restart to run the updated version
    else:
        exit_code = ok_return_code

    output = {"name": __application_name__, "version": __version__, "exit_code": exit_code, "pyshipupdate_version": pyshipupdate_version}
    print(json.dumps(output))
    sys.exit(exit_code)
"""

# no updater
app_code_basic = """
import json
import sys

from .__init__ import __application_name__, __version__, __author__

def app():

    output = {"name": __application_name__, "version": __version__, "exit_code": exit_code}
    print(json.dumps(output))
    sys.exit(exit_code)
"""

def make_test_app(destination_path: Path, app_name: str, app_version: str | VersionInfo, minimum_python_version: str, updater: bool):
    """
    Given a destination path, this function creates a simple Python application that can be used for testing purposes.
    It includes the test application package and pyproject.toml file.
    """

    if destination_path.exists():
        shutil.rmtree(destination_path)
    destination_path.mkdir(parents=True)

    python_version_no_dots = minimum_python_version.replace(".", "")

    # make the test application
    test_app_package_directory = Path(destination_path, app_name)
    test_app_package_directory.mkdir(parents=True)

    # __init__.py
    init_py = []
    init_py.append(f'__application_name__="{app_name}"')
    init_py.append(f'__author__="{__author__}"')  # use the same author as pyship
    init_py.append(f'__version__="{app_version}"')
    Path(test_app_package_directory, "__init__.py").write_text("\n".join(init_py))

    # __main__.py
    main_py = []
    main_py.append("from .app import app")
    main_py.append("from ismain import is_main")
    main_py.append("")
    main_py.append("if is_main():")
    main_py.append("    app()")
    Path(test_app_package_directory, "__main__.py").write_text("\n".join(main_py))

    # pyproject.toml
    pyproject_toml = []
    pyproject_toml.append("[project]")
    pyproject_toml.append(f'name = "{app_name}"')
    pyproject_toml.append(f'version = "{app_version}"')
    pyproject_toml.append('description = "A test application for pyship"')
    pyproject_toml.append(f'requires-python = ">={minimum_python_version}"')
    pyproject_toml.append('dependencies = ["ismain", "pyshipupdate", "sentry-sdk"]')
    pyproject_toml.append("")
    pyproject_toml.append('[[project.authors]]')
    pyproject_toml.append('name = "abel"')
    pyproject_toml.append('email = "noreply@abel.co"')
    pyproject_toml.append("")
    pyproject_toml.append("[tool.pyship]")
    pyproject_toml.append("# while most apps will be GUI apps, for testing tstpyshipapp is a CLI app")
    pyproject_toml.append("is_gui = false")
    Path(destination_path, "pyproject.toml").write_text("\n".join(pyproject_toml))

    # LICENSE file
    license_text = "MIT License"
    Path(destination_path, "LICENSE").write_text(license_text)

    # app
    app_code = app_code_updater if updater else app_code_basic
    Path(test_app_package_directory, "app.py").write_text(app_code)

    # make venv
    make_venv = []
    make_venv.append(f'"\\Program Files\\Python{python_version_no_dots}\python.exe" -m venv venv')
    make_venv.append("venv\\Scripts\\python.exe -m pip install --upgrade pip")
    make_venv.append("venv\\Scripts\\pip install .")
    Path(destination_path, "make_venv.bat").write_text("\n".join(make_venv))
