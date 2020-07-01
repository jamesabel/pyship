from pprint import pprint
from setuptools import setup, find_packages

from pyship import __application_name__, __author__, __version__

requirements = ["setuptools", "wheel", "ismain", "balsa", "requests", "attrs", "typeguard", "toml", "pyinstaller", "semver"]

packages = find_packages(where=__application_name__)

pprint(f"{packages=}")

setup(
    name=__application_name__,
    version=__version__,
    author=__author__,

    package_dir={'': __application_name__},
    packages=packages,

    package_data={
        "": ["pyship.ico"],  # does not work todo: fix it
    },

    install_requires=requirements
)
