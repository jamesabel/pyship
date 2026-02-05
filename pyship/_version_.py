from importlib.metadata import metadata

_metadata = metadata("pyship")

__application_name__ = "pyship"
__version__ = _metadata["Version"]
__author__ = _metadata["Author-email"].split("<")[0].strip() if "<" in _metadata["Author-email"] else _metadata["Author-email"]
__title__ = __application_name__
__author_email__ = _metadata["Author-email"]
__url__ = "https://github.com/jamesabel/pyship"
__download_url__ = "https://github.com/jamesabel/pyship"
__description__ = _metadata["Summary"]
