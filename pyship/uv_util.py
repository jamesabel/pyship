import platform
import shutil
import subprocess
import time
import zipfile
from pathlib import Path

from typeguard import typechecked
from balsa import get_logger

from pyship import __application_name__, pyship_print

log = get_logger(__application_name__)

UV_GITHUB_RELEASE_URL = "https://github.com/astral-sh/uv/releases/latest/download"
UV_CACHE_MAX_AGE_SECONDS = 7 * 24 * 60 * 60  # 7 days


@typechecked
def find_or_bootstrap_uv(cache_dir: Path) -> Path:
    """
    Find uv on PATH, in cache (if not stale), or download the standalone binary.
    Cached uv binaries are re-downloaded after 7 days.
    :param cache_dir: directory to cache the uv binary
    :return: path to the uv executable
    """
    # check PATH first
    uv_on_path = shutil.which("uv")
    if uv_on_path is not None:
        uv_path = Path(uv_on_path)
        log.info(f"found uv on PATH: {uv_path}")
        return uv_path

    # check cache (with TTL)
    uv_cache_dir = Path(cache_dir, "uv")
    uv_exe = Path(uv_cache_dir, "uv.exe")
    if uv_exe.exists():
        age_seconds = time.time() - uv_exe.stat().st_mtime
        age_days = age_seconds / 86400
        if age_seconds < UV_CACHE_MAX_AGE_SECONDS:
            log.info(f"found cached uv: {uv_exe} (age: {age_days:.1f} days)")
            return uv_exe
        else:
            pyship_print(f"cached uv is stale ({age_days:.0f} days old), re-downloading")

    # download uv standalone binary
    pyship_print("downloading uv")
    uv_cache_dir.mkdir(parents=True, exist_ok=True)

    machine = platform.machine().lower()
    if machine in ("amd64", "x86_64"):
        arch = "x86_64"
    elif machine in ("arm64", "aarch64"):
        arch = "aarch64"
    else:
        arch = machine

    zip_name = f"uv-{arch}-pc-windows-msvc.zip"
    zip_url = f"{UV_GITHUB_RELEASE_URL}/{zip_name}"
    zip_path = Path(uv_cache_dir, zip_name)

    import requests

    response = requests.get(zip_url, stream=True)
    response.raise_for_status()
    with open(zip_path, "wb") as f:
        shutil.copyfileobj(response.raw, f)

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(uv_cache_dir)

    # the zip extracts into a subdirectory; find uv.exe
    if not uv_exe.exists():
        for candidate in uv_cache_dir.rglob("uv.exe"):
            shutil.move(str(candidate), str(uv_exe))
            break

    if not uv_exe.exists():
        raise FileNotFoundError(f"could not find uv.exe after extracting {zip_path}")

    log.info(f"downloaded uv to {uv_exe}")
    return uv_exe


@typechecked
def uv_python_install(uv_path: Path, python_version: str) -> Path:
    """
    Install a Python version via uv and return its path.
    :param uv_path: path to uv executable
    :param python_version: Python version string (e.g. "3.12.4")
    :return: path to the installed Python interpreter
    """
    pyship_print(f"installing Python {python_version} via uv")
    subprocess.run([str(uv_path), "python", "install", python_version], check=True, capture_output=True, text=True)

    result = subprocess.run([str(uv_path), "python", "find", python_version], check=True, capture_output=True, text=True)
    python_path = Path(result.stdout.strip())
    log.info(f"uv python find {python_version} -> {python_path}")
    return python_path


@typechecked
def copy_standalone_python(uv_path: Path, python_version: str, dest_dir: Path) -> Path:
    """
    Copy a full standalone Python installation into dest_dir.
    Uses uv python install to ensure the Python is available, then copies the
    entire installation directory so the CLIP has no dependency on the base Python path.
    :param uv_path: path to uv executable
    :param python_version: Python version string (e.g. "3.12")
    :param dest_dir: destination directory to copy the Python installation into
    :return: path to python.exe inside dest_dir
    """
    python_path = uv_python_install(uv_path, python_version)
    python_install_dir = python_path.parent  # standalone Python has python.exe at root

    pyship_print(f'copying standalone Python from "{python_install_dir}" to "{dest_dir}"')
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    shutil.copytree(str(python_install_dir), str(dest_dir))

    # Remove EXTERNALLY-MANAGED marker so uv pip install works
    externally_managed = Path(dest_dir, "Lib", "EXTERNALLY-MANAGED")
    if externally_managed.exists():
        externally_managed.unlink()
        log.info(f"removed {externally_managed}")

    dest_python = Path(dest_dir, "python.exe")
    if not dest_python.exists():
        raise FileNotFoundError(f"python.exe not found at {dest_python} after copying standalone Python")

    # Verify the copied Python interpreter actually works
    verify_result = subprocess.run([str(dest_python), "-c", "import sys; print(sys.version)"], capture_output=True, text=True)
    if verify_result.returncode != 0:
        log.error(f"copied Python at {dest_python} failed verification (exit {verify_result.returncode}): {verify_result.stderr}")
        raise RuntimeError(f"copied Python interpreter at {dest_python} does not work (exit code {verify_result.returncode}): {verify_result.stderr}")
    log.info(f"copied Python verified: {verify_result.stdout.strip()}")

    log.info(f"standalone Python copied to {dest_dir}")
    return dest_python


@typechecked
def uv_pip_install(uv_path: Path, target_python: Path, packages: list, dist_dir: Path, upgrade: bool = True, system: bool = False) -> None:
    """
    Install packages into a Python environment using uv pip.
    :param uv_path: path to uv executable
    :param target_python: path to the Python interpreter in the target environment
    :param packages: list of package names or paths to install
    :param dist_dir: directory containing wheels to pass as --find-links
    :param upgrade: whether to pass -U flag
    :param system: whether to pass --system flag (required for non-venv Python installations)
    """
    cmd = [str(uv_path), "pip", "install", "--python", str(target_python)]
    if system:
        cmd.append("--system")
    if upgrade:
        cmd.append("-U")
    cmd.extend(packages)
    if dist_dir.exists():
        cmd.extend(["-f", str(dist_dir)])
    log.info(f"uv pip install cmd: {cmd}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    log.info(result.stdout)
    if result.stderr:
        log.info(result.stderr)
    if result.returncode != 0:
        log.error(f"uv pip install failed (exit {result.returncode}): {result.stderr}")
        result.check_returncode()


@typechecked
def uv_build(uv_path: Path, project_dir: Path, output_dir: Path) -> Path:
    """
    Build a wheel using uv build.
    :param uv_path: path to uv executable
    :param project_dir: project directory containing pyproject.toml
    :param output_dir: directory for the built wheel
    :return: path to the built wheel
    """
    pyship_print(f'building wheel via uv in "{project_dir}"')
    output_dir.mkdir(parents=True, exist_ok=True)
    cmd = [str(uv_path), "build", "--wheel", "--out-dir", str(output_dir)]
    log.info(f"uv build cmd: {cmd}")
    result = subprocess.run(cmd, cwd=str(project_dir), check=True, capture_output=True, text=True)
    log.info(result.stdout)

    # find the wheel that was just built
    wheels = list(output_dir.glob("*.whl"))
    if len(wheels) == 0:
        raise FileNotFoundError(f"no wheel found in {output_dir} after uv build")
    # return the most recently modified wheel
    return sorted(wheels, key=lambda p: p.stat().st_mtime)[-1]
