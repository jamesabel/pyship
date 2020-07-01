from setuptools import setup, find_packages

from pyship import __application_name__, __author__, __version__

requirements = ["setuptools", "wheel", "ismain", "balsa", "requests", "attrs", "typeguard", "toml", "pyinstaller", "semver"]

setup(
    name=__application_name__,
    version=__version__,
    author=__author__,

    package_dir={'': __application_name__},
    packages=find_packages(where=__application_name__),

    install_requires=requirements
)
