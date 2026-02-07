from pathlib import Path

import toml

from pyship import PyShip, __application_name__, __author__, PyshipLog, get_arguments, pyship_print, DEFAULT_DIST_DIR_NAME


def read_pyship_config() -> dict:
    """
    Read [tool.pyship] section from pyproject.toml in the current working directory.
    Returns only PyShip-level keys (not AppInfo-level keys like is_gui, run_on_startup).
    :return: dict of PyShip-level config values
    """
    pyproject_path = Path("pyproject.toml")
    config = {}
    if pyproject_path.exists():
        with pyproject_path.open() as f:
            pyproject = toml.load(f)
        tool_section = pyproject.get("tool", {})
        pyship_section = tool_section.get("pyship", {})
        # Only extract PyShip-level keys (not AppInfo-level keys like is_gui, run_on_startup)
        for key in ("name", "profile", "upload", "public_readable", "dist", "find_links"):
            if key in pyship_section:
                config[key] = pyship_section[key]
    return config


def main():
    args = get_arguments()

    pyship_log = PyshipLog(__application_name__, __author__)  # type: ignore[unknown-argument]
    pyship_log.init_logger_from_args(args)

    pyship_print(f"log_path={pyship_log.log_path}")

    pyship = PyShip()

    # Apply [tool.pyship] settings from pyproject.toml
    config = read_pyship_config()
    if "name" in config:
        pyship.name = config["name"]
    if "profile" in config:
        pyship.cloud_profile = config["profile"]
    if "upload" in config:
        pyship.upload = config["upload"]
    if "public_readable" in config:
        pyship.public_readable = config["public_readable"]
    if "dist" in config:
        pyship.dist_dir = Path(config["dist"])
    if "find_links" in config:
        pyship.find_links = config["find_links"]

    # CLI args override pyproject.toml values
    if args.name is not None:
        pyship.name = args.name
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
    if args.public_readable:
        pyship.public_readable = True
    if args.dist != DEFAULT_DIST_DIR_NAME:
        pyship.dist_dir = Path(args.dist)
    pyship.ship()
