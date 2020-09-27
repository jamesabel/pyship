from pyship import PyShip, __application_name__, __author__, PyshipLog, arguments, pyship_print


def main():

    args = arguments()

    pyship_log = PyshipLog(__application_name__, __author__)
    pyship_log.init_logger_from_args(args)

    pyship_print(f"log_path={pyship_log.log_path}")

    pyship = PyShip()
    if args.name is not None:
        pyship.name = args.name  # optionally get the target application name from the command line
    pyship.ship_installer()
