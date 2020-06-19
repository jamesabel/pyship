# pyship User Guide

## Goals

- Ship any Python application
- Enable application updates

### Non-Goals

- Compact installer size
- A variety of OSs (just Windows for now)
- 32 bit OS

## Terminology

- Target application - the application you want to ship 
- Project directory - the root project directory

## Flow

1) Create a target application as a Python package that runs as main using the `python -m <module>` argument.
2) Install pyship via pip, e.g. `python -m pip install pyship`
3) Create a `pyproject.toml` file (see [pyproject.toml](#pyproject.toml))
4) Run pyship, e.g. `python -m pyship`.  This will create the application installer.

## Application Requirements

- The application must be a Python package (e.g. is in a directory and has a `__init__.py` )
- Have a `__main__.py` file (so it can be run as `python -m <module>` )
- Have a `__version__` string at the package top level
- Have a `pyproject.toml` file
 
### pyproject.toml 

The `pyproject.toml` file must be in the project's root directory.  It must have a `[project]` section with `name` and `author` key/value pairs:

```
[project]
name = <string>>     # put in your application name here
author = <string>    # put in your author name here
```

`pyproject.toml` can optionally have a `[tool.pyship]` section:

```
[tool.pyship]
is_gui = <boolean>   # true for GUI app, false for CLI
```

# Supported Platforms and Requirements

- Windows 10/Windows Server 2019 (may work with other Windows versions)
- 64 bits
- [Python 3.8](https://www.python.org/downloads/) (may work with later Python versions))
- [NSIS (Nullsoft Scriptable Install System)](https://nsis.sourceforge.io/)

# Related Works

- [pynsist](https://pynsist.readthedocs.io/en/latest/)
- [pyinstaller](https://www.pyinstaller.org/)
- [briefcase](https://beeware.org/project/projects/tools/briefcase/)
