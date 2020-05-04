from pathlib import Path
import shutil
import tkinter

from typeguard import typechecked

from pyship import is_windows


@typechecked(always=True)
def copy_tree(source: Path, dest: Path, subdir: str):
    # copy the tree, but don't copy things like __pycache__
    dest.mkdir(parents=True, exist_ok=True)
    source = Path(source, subdir)
    dest = Path(dest, subdir)
    shutil.copytree(str(source), str(dest), ignore=shutil.ignore_patterns("__pycache__"), dirs_exist_ok=True)


@typechecked(always=True)
def add_tkinter(pyshipy: Path):
    # the embedded Python doesn't ship with tkinter, so add it to pyshipy
    # https://stackoverflow.com/questions/37710205/python-embeddable-zip-install-tkinter

    if is_windows():
        python_base_install_dir = Path(tkinter.__file__).parent.parent.parent

        copy_tree(Path(python_base_install_dir), pyshipy, "tcl")  # tcl dir
        copy_tree(Path(python_base_install_dir, "Lib"), Path(pyshipy, "Lib", "site-packages"), "tkinter")  # tkinter dir

        # dlls
        for file_name in ["_tkinter.pyd", "tcl86t.dll", "tk86t.dll"]:
            shutil.copy2(str(Path(python_base_install_dir, "DLLs", file_name)), str(pyshipy))
