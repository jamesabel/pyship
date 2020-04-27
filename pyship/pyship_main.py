import argparse

from balsa import verbose_arg_string, log_dir_arg_string, delete_existing_arg_string

from pyship import PyShip, __application_name__, __version__, PyshipLog


def pyship_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-V', '--version', dest="version", action='store_true', help='display version')
    parser.add_argument('-v', f"--{verbose_arg_string}", dest=verbose_arg_string, action='store_true', help='verbose')
    parser.add_argument('-l', f"--{log_dir_arg_string}", dest=log_dir_arg_string, help="log directory")
    parser.add_argument("-d", f"--{delete_existing_arg_string}", dest=delete_existing_arg_string, action='store_true', help="delete existing log")
    args = parser.parse_args()

    if args.version:
        print(__version__)
    else:
        pyship_log = PyshipLog(__application_name__, __version__)
        pyship_log.init_logger_from_args(args)

        pyship = PyShip()
        pyship.ship()
