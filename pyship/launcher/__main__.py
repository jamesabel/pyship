import sys

from ismain import is_main

from .launcher import launch

if is_main():
    sys.exit(launch())
