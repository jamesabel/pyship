import json
import sys

from balsa import Balsa, get_logger

from pyshipupdate import UpdaterAwsS3
from pyship import restart_return_code, ok_return_code
from pyship import __author__ as pyship_author

from .__init__ import __application_name__ as name
from .__init__ import __version__ as version

logger_name = f"{name}_{version}"

log = get_logger(logger_name)


def tstpyshipapp():

    verbose = len(sys.argv) > 1 and (sys.argv[1].lower() == "-v" or sys.argv[1].lower() == "--verbose")

    balsa = Balsa(logger_name, pyship_author, verbose=verbose)
    balsa.init_logger()

    updater = UpdaterAwsS3(name)
    if updater.update(version):
        exit_code = restart_return_code  # app has been updated so restart to run the updated version
    else:
        exit_code = ok_return_code

    output = {"name": name, "version": version, "exit_code": exit_code}
    print(json.dumps(output))
    sys.exit(exit_code)
