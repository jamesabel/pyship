import argparse

from balsa import verbose_arg_string, log_dir_arg_string, delete_existing_arg_string

from pyship import PyShip, __application_name__, __version__, PyshipLog, arguments


def main():

    args = arguments()

    pyship_log = PyshipLog(__application_name__, __version__)
    pyship_log.init_logger_from_args(args)

    pyship = PyShip()
    pyship.ship_installer()
