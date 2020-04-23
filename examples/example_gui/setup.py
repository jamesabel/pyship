import os

from setuptools import setup

from example_gui import __application_name__, __version__, __author__, __author_email__, __url__, __download_url__, __description__

readme_file_path = os.path.join(__application_name__, "readme.md")

with open(readme_file_path, encoding="utf-8") as f:
    long_description = "\n" + f.read()

setup(
    name=__application_name__,
    description=__description__,
    long_description=long_description,
    long_description_content_type="text/x-rst",
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    license="MIT License",
    url=__url__,
    download_url=__download_url__,
    keywords=["example", "gui"],
    packages=[__application_name__],
    package_data={__application_name__: [readme_file_path]},
    install_requires=["ismain", "PyQt5"],  # for now pyship has to be installed separately, until it's on PyPI
    classifiers=[],
)
