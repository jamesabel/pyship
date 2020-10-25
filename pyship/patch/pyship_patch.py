def pyship_patch():
    # this is a function in order to load its source (via inspect.getsource() ), that is written to pyship_patch.py (without the function definition)

    # I got this error:
    #    "AttributeError: 'zipimporter' object has no attribute 'exec_module'"
    #
    # and found this workaround which is implemented below
    # https://stackoverflow.com/questions/63574951/cant-start-python-script-in-android-studio-via-chaquopy-after-including-datepar
    #
    # along with this hack to implement it in the Python environment:
    # https://nedbatchelder.com/blog/201001/running_code_at_python_startup.html
    #
    # this must accompany pyship_patch.pth (i.e. in the same directory) to load this upon Python interpreter startup.  In other words, they both must be put in the clip directory
    # (where python.exe resides).
    #
    # pyship_patch.pth contents:
    #
    #   import pyship_patch
    #
    from zipimport import zipimporter

    def create_module(self, spec):
        return None

    zipimporter.create_module = create_module

    def exec_module(self, module):
        exec(self.get_code(module.__name__), module.__dict__)

    zipimporter.exec_module = exec_module


pyship_patch()
