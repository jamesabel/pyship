import json
import sys

from pyship import restart_return_code, ok_return_code, UpdaterAwsS3

from .__init__ import __application_name__ as name
from .__init__ import __version__ as version


def tstpyshipapp():

    updater = UpdaterAwsS3(name)
    updater.packaged_app_dirs.add()

    if updater.update():
        exit_code = restart_return_code  # app has been updated so restart to run the updated version
    else:
        exit_code = ok_return_code

    print(json.dumps({"name": name, "version": version}, indent=4))
    sys.exit(exit_code)
