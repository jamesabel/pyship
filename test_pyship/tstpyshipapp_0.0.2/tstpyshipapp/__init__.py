""" An app used to test pyship """

__application_name__ = "tstpyshipapp"

# normally we'd use
#    from .__version__ import __version__
# however this doesn't work in our test infrastructure since importlib.import_module() or even importlib.reload() does not reload relative imports
# this should not be a problem for regular users since we expect that they will only be importing one version of their program for a particular run
__version__ = "0.0.2"
