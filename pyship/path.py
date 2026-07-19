"""
NullPath: a sentinel Path subclass for not-yet-initialized path fields.
"""

from pathlib import Path


# Path doesn't allow for direct sub-typing, but this is a workaround:
class NullPath(type(Path())):  # type: ignore
    """A "null" Path: has Path's type but is not initialized to an actual OS path yet."""

    pass
