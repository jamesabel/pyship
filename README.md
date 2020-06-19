# pyship

Enables shipping a python application to end users.

# Terminology

- Target application - the application you want to ship 
- Project directory - the root project directory

# Flow

1) Create a target application as a Python package that runs as main using the `python -m <module>` argument.
2) Install pyship via pip, e.g. `python -m pip install pyship`
3) Create a `pyproject.toml` file (see [pyproject.toml](#pyproject.toml))

# Application Requirements

- Is a Python package (e.g. is in a directory and has a `__init__.py` )
- Has a `__main__.py` file (so it can be run as `python -m <module>` )
- Has a `__version__` string at the package top level
- Has a `pyproject.toml` file
 
## pyproject.toml 

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
