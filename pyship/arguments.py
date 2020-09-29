import sys
import argparse

from balsa import verbose_arg_string, delete_existing_arg_string, log_dir_arg_string

from pyship import __name__, __version__, DEFAULT_DIST_DIR_NAME


def arguments():

    parser = argparse.ArgumentParser(prog=__name__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("-n", "--name", help='name of target application to ship (if not provided elsewhere such as in pyproject.toml at: [project] name=<name>')
    parser.add_argument("-d", "--dist", default=DEFAULT_DIST_DIR_NAME, help="distribution directory for this target application (i.e. directory that contains the wheel)")
    parser.add_argument("-f", "--findlinks", nargs='+', default=[],
                        help="one or more directories to pass to pip when creating the lip (similar to pip's --find-links except only specify once for multiple directories)")

    parser.add_argument("--version", action="store_true", help="display version")
    parser.add_argument("-v", f"--{verbose_arg_string}", action="store_true", help="increase output verbosity")
    parser.add_argument(f"--{delete_existing_arg_string}", action="store_true", help="delete log prior to running")
    parser.add_argument(f"--{log_dir_arg_string}", help="force a particular log directory (default is appdir's log directory)")
    args = parser.parse_args()

    if args.version:
        print(f"{__name__} {__version__}")
        sys.exit()

    return args
