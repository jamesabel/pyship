from pathlib import Path


# Path doesn't allow for sub-typing, but this is a workaround:
class NullPath(type(Path())):  # type: ignore
    # A "null" Path. Used to represent a class of type Path but it's not initialized to a actual OS path yet.
    pass
