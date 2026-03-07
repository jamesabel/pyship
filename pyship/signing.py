from pathlib import Path
from typing import Union

from typeguard import typechecked
from balsa import get_logger

from pyship import __application_name__
from pyship.custom_print import pyship_print
from pyship.subprocess import subprocess_run

log = get_logger(__application_name__)

_SDK_BIN_DIR = Path(r"C:\Program Files (x86)\Windows Kits\10\bin")


@typechecked
def _find_signtool(_sdk_bin_dir: Path = _SDK_BIN_DIR) -> Union[Path, None]:
    """
    Locate signtool.exe from the Windows SDK bin directory.
    :param _sdk_bin_dir: Windows SDK bin directory to search
    :return: path to signtool.exe with the highest SDK version, or None if not found
    """
    if not _sdk_bin_dir.is_dir():
        return None

    candidates = []
    for child in _sdk_bin_dir.iterdir():
        if child.is_dir() and child.name.startswith("10."):
            signtool = Path(child, "x64", "signtool.exe")
            if signtool.exists():
                try:
                    version_tuple = tuple(int(x) for x in child.name.split("."))
                    candidates.append((version_tuple, signtool))
                except ValueError:
                    pass

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


@typechecked
def sign_file(file_path: Path, pfx_path: Path, certificate_password: str, timestamp_url: str, signtool_path: Union[Path, None] = None) -> bool:
    """
    Sign a file using signtool.exe with the given PFX certificate.
    :param file_path: path to the file to sign
    :param pfx_path: path to the PFX certificate file
    :param certificate_password: password for the PFX certificate
    :param timestamp_url: RFC 3161 timestamp server URL
    :param signtool_path: explicit path to signtool.exe; auto-discovered if None
    :return: True if signing succeeded, False otherwise
    """
    if signtool_path is None:
        signtool_path = _find_signtool()
    if signtool_path is None:
        log.warning("signtool.exe not found; skipping signing")
        return False

    if not file_path.exists():
        log.error(f"file to sign does not exist: {file_path}")
        return False
    if not pfx_path.exists():
        log.error(f"PFX certificate file does not exist: {pfx_path}")
        return False

    cmd = [str(signtool_path), "sign", "/f", str(pfx_path), "/p", certificate_password, "/tr", timestamp_url, "/td", "sha256", "/fd", "sha256", str(file_path)]
    return_code, _, _ = subprocess_run(cmd)
    if return_code == 0:
        pyship_print(f'signed "{file_path}"')
        return True
    else:
        log.warning(f"signtool returned exit code {return_code} for {file_path}")
        return False


@typechecked
def sign_if_configured(file_path: Union[Path, None], pfx_path: Union[Path, None], certificate_password: Union[str, None], timestamp_url: str, signtool_path: Union[Path, None] = None) -> bool:
    """
    Sign a file if signing is fully configured; silently skip otherwise.
    :param file_path: path to the file to sign, or None to skip
    :param pfx_path: path to the PFX certificate file, or None to skip
    :param certificate_password: password for the PFX certificate, or None to skip
    :param timestamp_url: RFC 3161 timestamp server URL
    :param signtool_path: explicit path to signtool.exe; auto-discovered if None
    :return: True if signing succeeded, False if skipped or failed
    """
    if file_path is None:
        log.debug("file_path is None; skipping signing")
        return False
    if pfx_path is None or certificate_password is None:
        log.warning("pfx_path or certificate_password not configured; skipping signing")
        return False
    return sign_file(file_path, pfx_path, certificate_password, timestamp_url, signtool_path)
