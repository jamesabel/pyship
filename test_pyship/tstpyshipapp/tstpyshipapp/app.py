import json
import sys

from .__version__ import __application_name__ as name
from .__version__ import __version__ as version


def tstpyshipapp():
    print(json.dumps({"name": name, "version": version}, indent=4))
    sys.exit(0)  # OK
