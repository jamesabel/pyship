from pathlib import Path
import shutil
import tkinter

from typeguard import typechecked


@typechecked(always=True)
def copy_tree(source: Path, dest: Path):
    shutil.copytree(str(source), str(dest), ignore=shutil.ignore_patterns("__pycache__"), dirs_exist_ok=True)


@typechecked(always=True)
def add_tkinter(pyshipy: Path):
    # the embedded Python doesn't ship with tkinter, so add it to pyshipy
    # https://stackoverflow.com/questions/37710205/python-embeddable-zip-install-tkinter

    python_base_install_dir = Path(tkinter.__file__).parent.parent.parent

    copy_tree(Path(python_base_install_dir, "tcl"), pyshipy)  # tcl dir
    copy_tree(Path(python_base_install_dir, "Lib", "tkinter"), Path(pyshipy, "Lib", "site-packages"))  # tkinter dir

    # dlls
    for file_name in ["_tkinter.pyd", "tcl86t.dll", "tk86t.dll"]:
        shutil.copy2(str(Path(python_base_install_dir, "DLLs", file_name)), str(pyshipy))
