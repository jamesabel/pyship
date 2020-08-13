from pyship import PyShip, __application_name__, __version__, PyshipLog, arguments


def main():

    args = arguments()

    pyship_log = PyshipLog(__application_name__, __version__)
    pyship_log.init_logger_from_args(args)

    pyship = PyShip()
    if args.name is not None:
        pyship.name = args.name  # optionally get the target application name from the command line
    pyship.ship_installer()
