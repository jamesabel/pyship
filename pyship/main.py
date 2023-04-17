from pyship import PyShip, __application_name__, __author__, PyshipLog, get_arguments, pyship_print


def main():
    args = get_arguments()

    pyship_log = PyshipLog(__application_name__, __author__)
    pyship_log.init_logger_from_args(args)

    pyship_print(f"log_path={pyship_log.log_path}")

    pyship = PyShip()
    if args.name is not None:
        pyship.name = args.name  # optionally get the target application name from the command line
    if args.findlinks is not None and len(args.findlinks) > 0:
        pyship.find_links = args.findlinks
    if args.profile is not None:
        pyship.cloud_profile = args.profile
    if args.id is not None:
        pyship.cloud_id = args.id
    if args.secret is not None:
        pyship.cloud_secret = args.secret
    if args.noupload:
        pyship.upload = False
    pyship.ship()
