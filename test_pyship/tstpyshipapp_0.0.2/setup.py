from setuptools import setup, find_packages

requirements = ["balsa", "pyship"]

setup(
    name="tstpyshipapp",
    version="0.0.2",
    author="abel",
    author_email="j@abel.co",
    description="pyship test app 0.0.2",  # called summary in the wheel

    packages=find_packages(),

    package_data={
        "": ["*.ico"],
    },

    install_requires=requirements
)
