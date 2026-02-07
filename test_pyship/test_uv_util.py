import platform
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from ismain import is_main
from balsa import get_logger

from pyship import PyshipLog, __author__
from pyship.uv_util import find_or_bootstrap_uv, uv_python_install, uv_venv_create, uv_pip_install

from test_pyship import __application_name__

log = get_logger(__application_name__)


def test_find_or_bootstrap_uv():
    with TemporaryDirectory() as tmp:
        cache_dir = Path(tmp, "cache")
        uv_path = find_or_bootstrap_uv(cache_dir)
        assert uv_path.exists()
        log.info(f"{uv_path=}")


def test_uv_venv_create():
    python_ver_tuple = platform.python_version_tuple()
    python_version = f"{python_ver_tuple[0]}.{python_ver_tuple[1]}"

    with TemporaryDirectory() as tmp:
        cache_dir = Path(tmp, "cache")
        venv_dir = Path(tmp, "test_venv")

        uv_path = find_or_bootstrap_uv(cache_dir)
        uv_python_install(uv_path, python_version)
        uv_venv_create(uv_path, venv_dir, python_version)

        assert Path(venv_dir, "Scripts", "python.exe").exists()
        assert Path(venv_dir, "pyvenv.cfg").exists()


def test_uv_pip_install():
    python_ver_tuple = platform.python_version_tuple()
    python_version = f"{python_ver_tuple[0]}.{python_ver_tuple[1]}"

    with TemporaryDirectory() as tmp:
        cache_dir = Path(tmp, "cache")
        venv_dir = Path(tmp, "test_venv")

        uv_path = find_or_bootstrap_uv(cache_dir)
        uv_python_install(uv_path, python_version)
        uv_venv_create(uv_path, venv_dir, python_version)

        target_python = Path(venv_dir, "Scripts", "python.exe")
        uv_pip_install(uv_path, target_python, ["ismain"], Path(tmp, "dist"), upgrade=True)

        assert Path(venv_dir, "Lib", "site-packages", "ismain").exists()


if is_main():
    pyship_log = PyshipLog(__application_name__, __author__, log_directory="log", delete_existing_log_files=True, verbose=True)
    pyship_log.init_logger()
    test_find_or_bootstrap_uv()
    test_uv_venv_create()
    test_uv_pip_install()
