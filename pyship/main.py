"""
CLI entry point for ``python -m pyship``.

Reads configuration from ``[tool.pyship]`` in the current directory's
``pyproject.toml``, applies CLI argument overrides, then runs :meth:`PyShip.ship`.
"""

from pathlib import Path

import toml

from pyship import PyShip, __application_name__, __author__, PyshipLog, get_arguments, pyship_print

#: pyproject.toml keys (under ``[tool.pyship]``) that map directly to PyShip attributes.
#: Keys whose PyShip attribute name differs use ``(toml_key, attr_name)`` tuples.
_TOML_KEYS = [
    ("profile", "cloud_profile"),
    ("upload", "upload"),
    ("public_readable", "public_readable"),
    ("certificate_sha1", "certificate_sha1"),
    ("certificate_subject", "certificate_subject"),
    ("certificate_auto_select", "certificate_auto_select"),
    ("code_sign", "code_sign"),
]


def read_pyship_config() -> dict:
    """
    Read ``[tool.pyship]`` section from ``pyproject.toml`` in the current working directory.

    Only extracts PyShip-level keys (not AppInfo-level keys like ``ui`` or ``run_on_startup``).

    :return: dict mapping PyShip attribute names to their configured values
    """
    pyproject_path = Path("pyproject.toml")
    config = {}
    if pyproject_path.exists():
        with pyproject_path.open() as f:
            pyproject = toml.load(f)
        pyship_section = pyproject.get("tool", {}).get("pyship", {})
        for toml_key, attr_name in _TOML_KEYS:
            if toml_key in pyship_section:
                config[attr_name] = pyship_section[toml_key]
    return config


def main():
    args = get_arguments()

    pyship_log = PyshipLog(__application_name__, __author__)  # type: ignore[unknown-argument]
    pyship_log.init_logger_from_args(args)

    pyship_print(f"log_path={pyship_log.log_path}")

    pyship = PyShip()

    # Apply [tool.pyship] settings from pyproject.toml
    config = read_pyship_config()
    for attr_name, value in config.items():
        setattr(pyship, attr_name, value)

    # CLI args override pyproject.toml values
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
    if args.pfx_path is not None:
        pyship.pfx_path = Path(args.pfx_path)
    if args.certificate_password is not None:
        pyship.certificate_password = args.certificate_password
    if args.certificate_sha1 is not None:
        pyship.certificate_sha1 = args.certificate_sha1
    if args.certificate_subject is not None:
        pyship.certificate_subject = args.certificate_subject
    if args.certificate_auto_select:
        pyship.certificate_auto_select = True
    if args.code_sign:
        pyship.code_sign = True
    pyship.ship()
