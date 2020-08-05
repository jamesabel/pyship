import sys
import argparse

from balsa import verbose_arg_string, delete_existing_arg_string, log_dir_arg_string

from pyship import __name__, __version__, DEFAULT_DIST_DIR_NAME


def arguments():

    parser = argparse.ArgumentParser(prog=__name__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-a", "--application", help="name of target application to ship")
    parser.add_argument("-d", "--dist", default=DEFAULT_DIST_DIR_NAME, help="distribution directory for this target application that contains the wheel")

    parser.add_argument("--version", action="store_true", help="display version")
    parser.add_argument("-v", f"--{verbose_arg_string}", action="store_true", help="increase output verbosity")
    parser.add_argument(f"--{delete_existing_arg_string}", action="store_true", help="delete log prior to running")
    parser.add_argument(f"--{log_dir_arg_string}", help="log directory")
    args = parser.parse_args()

    if args.version:
        print(f"{__name__} {__version__}")
        sys.exit()

    return args