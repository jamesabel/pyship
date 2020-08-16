from setuptools import setup, find_packages

from pyship import __application_name__, __author__, __version__

requirements = ["setuptools", "wheel", "ismain", "balsa", "requests", "attrs", "typeguard", "toml", "pyinstaller", "semver", "python-dateutil", "wheel-inspect", "boto3"]

setup(
    name=__application_name__,
    version=__version__,
    author=__author__,

    packages=find_packages(exclude=["test_*"]),

    package_data={
        "": ["*.ico"],
    },

    install_requires=requirements
)
