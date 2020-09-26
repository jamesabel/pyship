from setuptools import setup

from pyship import __application_name__, __author__, __version__

requirements = ["setuptools", "wheel", "ismain", "balsa", "requests", "attrs", "typeguard", "toml", "pyinstaller", "semver", "python-dateutil", "wheel-inspect", "boto3", "awsimple"]

setup(
    name=__application_name__,
    version=__version__,
    author=__author__,

    packages=[__application_name__, f"{__application_name__}.launcher", f"{__application_name__}.updater", f"{__application_name__}.aws"],

    package_data={
        "": ["*.ico"],
    },

    install_requires=requirements
)
