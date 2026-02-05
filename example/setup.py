from setuptools import setup, find_packages

requirements = ["PySide6", "ismain"]

setup(
    name="pyshipexample",
    version="0.0.1",
    author="abel",
    author_email="j@abel.co",
    description="Example PySide6 GUI application for pyship",
    packages=find_packages(),
    install_requires=requirements,
)
