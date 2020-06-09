import json
import sys
from pathlib import Path

from pyship import restart_return_code, ok_return_code, UpdaterAwsS3

from .__init__ import __application_name__ as name
from .__init__ import __version__ as version


def tstpyshipapp():

    updater = UpdaterAwsS3(name)
    dist_path = Path("test_pyship", "tstpyshipapp_0.0.1", "dist").resolve().absolute()
    updater.packaged_app_dirs.add(dist_path)

    if updater.update():
        exit_code = restart_return_code  # app has been updated so restart to run the updated version
    else:
        exit_code = ok_return_code

    print(json.dumps({"name": name, "version": version}, indent=4))
    sys.exit(exit_code)
