import json
import sys
from pathlib import Path

from balsa import Balsa, get_logger

from pyship import restart_return_code, ok_return_code, APP_DIR_NAME
from pyship import __application_name__ as pyship_application_name
from pyship.updater import UpdaterLocal
from pyship import __author__ as pyship_author

from .__init__ import __application_name__ as name
from .__init__ import __version__ as version

logger_name = f"{name}_{version}"

log = get_logger(logger_name)


def tstpyshipapp():

    verbose = len(sys.argv) > 1 and (sys.argv[1].lower() == "-v" or sys.argv[1].lower() == "--verbose")

    balsa = Balsa(logger_name, pyship_author, verbose=verbose)
    balsa.init_logger()

    updater = UpdaterLocal(name)
    updated_app_path = Path(Path.home(), "projects", pyship_application_name,  "test_pyship", f"{name}_0.0.2", APP_DIR_NAME, name).resolve().absolute()
    log.info(f"{updated_app_path=}")
    updater.app_dirs.add(updated_app_path)

    if updater.update(version):
        exit_code = restart_return_code  # app has been updated so restart to run the updated version
    else:
        exit_code = ok_return_code

    output = {"name": name, "version": version, "exit_code": exit_code}
    print(json.dumps(output))
    sys.exit(exit_code)
