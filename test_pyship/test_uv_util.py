import platform
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from ismain import is_main
from balsa import get_logger

from pyship import PyshipLog, __author__
from pyship.uv_util import find_or_bootstrap_uv, uv_python_install, copy_standalone_python, uv_pip_install

from test_pyship import __application_name__

log = get_logger(__application_name__)


def test_find_or_bootstrap_uv():
    with TemporaryDirectory() as tmp:
        cache_dir = Path(tmp, "cache")
        uv_path = find_or_bootstrap_uv(cache_dir)
        assert uv_path.exists()
        log.info(f"{uv_path=}")


def test_copy_standalone_python():
    python_ver_tuple = platform.python_version_tuple()
    python_version = f"{python_ver_tuple[0]}.{python_ver_tuple[1]}"

    with TemporaryDirectory() as tmp:
        cache_dir = Path(tmp, "cache")
        dest_dir = Path(tmp, "test_python")

        uv_path = find_or_bootstrap_uv(cache_dir)
        python_exe = copy_standalone_python(uv_path, python_version, dest_dir)

        assert python_exe.exists()
        assert python_exe == Path(dest_dir, "python.exe")
        assert not Path(dest_dir, "pyvenv.cfg").exists()
        assert not Path(dest_dir, "Lib", "EXTERNALLY-MANAGED").exists()


def test_uv_pip_install():
    python_ver_tuple = platform.python_version_tuple()
    python_version = f"{python_ver_tuple[0]}.{python_ver_tuple[1]}"

    with TemporaryDirectory() as tmp:
        cache_dir = Path(tmp, "cache")
        dest_dir = Path(tmp, "test_python")

        uv_path = find_or_bootstrap_uv(cache_dir)
        target_python = copy_standalone_python(uv_path, python_version, dest_dir)

        uv_pip_install(uv_path, target_python, ["ismain"], Path(tmp, "dist"), upgrade=True, system=True)

        assert Path(dest_dir, "Lib", "site-packages", "ismain").exists()


if is_main():
    pyship_log = PyshipLog(__application_name__, __author__, log_directory="log", delete_existing_log_files=True, verbose=True)
    pyship_log.init_logger()
    test_find_or_bootstrap_uv()
    test_copy_standalone_python()
    test_uv_pip_install()
