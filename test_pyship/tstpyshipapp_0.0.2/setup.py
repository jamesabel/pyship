from setuptools import setup, find_packages

requirements = ["balsa", "pyship"]

setup(
    name="tstpyshipapp",
    version="0.0.2",
    author="abel",

    packages=find_packages(),

    package_data={
        "": ["*.ico"],
    },

    install_requires=requirements
)
