from setuptools import setup, find_packages

# moto is only in the requirements since we're testing - it won't be in normal apps
requirements = ["balsa", "pyshipupdate", "pyship", "moto", "sentry-sdk"]

setup(
    name="tstpyshipapp",
    version="0.0.1",
    author="abel",
    author_email="j@abel.co",
    description="pyship test app 0.0.1",  # called summary in the wheel
    packages=find_packages(),
    package_data={
        "": ["*.ico"],
    },
    install_requires=requirements,
)
