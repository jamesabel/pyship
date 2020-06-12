import json
import sys
from pathlib import Path

from pyship import restart_return_code, ok_return_code, UpdaterLocal, APP_DIR_NAME
from pyship import __application_name__ as pyship_application_name

from .__init__ import __application_name__ as name
from .__init__ import __version__ as version


def tstpyshipapp():

    updater = UpdaterLocal(name)
    updated_app_path = Path(Path.home(), "projects", pyship_application_name,  "test_pyship", f"{name}_0.0.2", APP_DIR_NAME, name).resolve().absolute()
    updater.app_dirs.add(updated_app_path)

    if updater.update(version):
        exit_code = restart_return_code  # app has been updated so restart to run the updated version
    else:
        exit_code = ok_return_code

    output = {"name": name, "version": version, "exit_code": exit_code}
    print(json.dumps(output))
    sys.exit(exit_code)
