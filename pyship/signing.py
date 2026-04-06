"""
Code signing for Windows executables via signtool.exe.

Supports two signing modes:
- **PFX mode**: sign with a .pfx certificate file and password
- **Token mode**: sign with a certificate from the Windows Certificate Store
  (hardware tokens such as Sectigo OV, SafeNet eToken, YubiKey)

Pre-flight detection functions verify that the signing infrastructure (PFX file,
smart-card hardware, certificate store entry) is available before signing begins.
"""

import hashlib
import ssl
import subprocess
import sys
from pathlib import Path
from typing import Union

if sys.platform == "win32":
    import ctypes

from typeguard import typechecked
from balsa import get_logger

from pyship import __application_name__
from pyship.custom_print import pyship_print
from pyship.subprocess import subprocess_run

log = get_logger(__application_name__)

_SDK_BIN_DIR = Path(r"C:\Program Files (x86)\Windows Kits\10\bin")


# ---------------------------------------------------------------------------
# Internal helpers (shared by PFX and token signing)
# ---------------------------------------------------------------------------


@typechecked
def _find_signtool(_sdk_bin_dir: Path = _SDK_BIN_DIR) -> Union[Path, None]:
    """
    Locate signtool.exe from the Windows SDK bin directory.
    Scans versioned subdirectories (e.g. ``10.0.22621.0``) and returns
    the ``x64/signtool.exe`` from the highest version found.

    :param _sdk_bin_dir: Windows SDK bin directory to search
    :return: path to signtool.exe, or None if not found
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
def _resolve_signtool(signtool_path: Union[Path, None]) -> Union[Path, None]:
    """
    Return a validated signtool.exe path, auto-discovering if *signtool_path* is None.

    :param signtool_path: explicit path, or None to auto-discover
    :return: resolved path, or None (with a warning logged) if not found
    """
    if signtool_path is None:
        signtool_path = _find_signtool()
    if signtool_path is None:
        log.warning("signtool.exe not found; skipping signing")
    return signtool_path


@typechecked
def _run_signtool(cmd: list, file_path: Path) -> bool:
    """
    Execute a signtool command and interpret the result.

    :param cmd: full command list (signtool.exe + arguments)
    :param file_path: the file being signed (for log messages)
    :return: True if signtool exited with code 0
    """
    return_code, _, _ = subprocess_run(cmd)
    if return_code == 0:
        pyship_print(f'signed "{file_path}"')
        return True
    log.warning(f"signtool returned exit code {return_code} for {file_path}")
    return False


@typechecked
def _validate_sha1(thumbprint: str) -> Union[str, None]:
    """
    Validate and normalise a SHA1 certificate thumbprint.

    :param thumbprint: raw thumbprint string (may contain spaces)
    :return: cleaned 40-char lowercase hex string, or None if invalid
    """
    clean = thumbprint.replace(" ", "")
    if len(clean) != 40 or not all(c in "0123456789abcdefABCDEF" for c in clean):
        log.error(f"invalid SHA1 thumbprint (expected 40 hex characters): {thumbprint!r}")
        return None
    return clean


# ---------------------------------------------------------------------------
# Token / smart-card detection
# ---------------------------------------------------------------------------


@typechecked
def is_token_present() -> bool:
    """
    Check if a smart card device is present via Windows PnP device enumeration.

    Runs ``Get-PnpDevice -Class SmartCard`` in PowerShell and looks for at
    least one device with ``Status == OK``.

    :return: True if a SmartCard-class device with Status OK is detected
    """
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Get-PnpDevice -Class SmartCard -ErrorAction SilentlyContinue | Where-Object { $_.Status -eq 'OK' } | Select-Object -ExpandProperty FriendlyName"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0 and result.stdout.strip():
            log.debug(f"smart card device(s) detected: {result.stdout.strip()}")
            return True
    except Exception as exc:
        log.debug(f"smart card detection failed: {exc}")
    log.debug("no smart card device detected")
    return False


@typechecked
def is_rdp_session() -> bool:
    """
    Detect if the current session is a Remote Desktop (RDP) session.

    Hardware token PIN dialogs do not work over RDP, and failed attempts
    count against the token lockout counter.

    Uses ``GetSystemMetrics(SM_REMOTESESSION)`` as primary detection,
    with ``query session`` command as fallback.

    :return: True if the session appears to be an RDP/remote session
    """
    # Primary: Win32 API
    try:
        SM_REMOTESESSION = 0x1000
        if ctypes.windll.user32.GetSystemMetrics(SM_REMOTESESSION) != 0:
            log.debug("RDP session detected via GetSystemMetrics(SM_REMOTESESSION)")
            return True
    except (AttributeError, NameError, OSError) as exc:
        log.debug(f"GetSystemMetrics check failed: {exc}")

    # Fallback: parse 'query session' output
    try:
        result = subprocess.run(["query", "session"], capture_output=True, text=True, timeout=10)
        if result.stdout:
            for line in result.stdout.splitlines():
                # Active session line starts with '>'
                if line.strip().startswith(">"):
                    session_name = line.strip().lstrip(">").split()[0].lower()
                    if session_name.startswith("rdp-"):
                        log.debug(f"RDP session detected via query session: {session_name}")
                        return True
    except Exception as exc:
        log.debug(f"query session check failed: {exc}")

    log.debug("no RDP session detected")
    return False


@typechecked
def is_certificate_in_store(certificate_sha1: Union[str, None] = None, certificate_subject: Union[str, None] = None) -> bool:
    """
    Check if a signing certificate is present in the Windows Certificate Store (MY).

    Uses :func:`ssl.enum_certificates` (stdlib, Windows-only) so no extra
    dependencies are required.

    :param certificate_sha1: SHA1 thumbprint (40-char hex) to match
    :param certificate_subject: subject common name to match (case-insensitive substring)
    :return: True if a matching certificate is found
    """
    if certificate_sha1 is None and certificate_subject is None:
        return False

    try:
        certs = ssl.enum_certificates("MY")
    except Exception as exc:
        log.debug(f"failed to enumerate certificates: {exc}")
        return False

    target_thumbprint = certificate_sha1.replace(" ", "").lower() if certificate_sha1 is not None else None
    target_subject = certificate_subject.lower() if certificate_subject is not None else None

    for cert_der, encoding_type, _trust in certs:
        if encoding_type != "x509_asn":
            continue
        if target_thumbprint is not None:
            thumbprint = hashlib.sha1(cert_der).hexdigest().lower()
            if thumbprint == target_thumbprint:
                log.debug(f"certificate with thumbprint {target_thumbprint} found in store")
                return True
        if target_subject is not None:
            # Best-effort subject match: check if the subject string appears in the DER-encoded cert.
            # This handles the common case without requiring the cryptography package.
            try:
                cert_text = cert_der.decode("ascii", errors="replace").lower()
                if target_subject in cert_text:
                    log.debug(f"certificate with subject containing {certificate_subject!r} found in store")
                    return True
            except Exception:
                pass

    log.debug("matching certificate not found in Windows Certificate Store")
    return False


@typechecked
def check_signing_available(
    pfx_path: Union[Path, None] = None,
    certificate_sha1: Union[str, None] = None,
    certificate_subject: Union[str, None] = None,
    certificate_auto_select: bool = False,
) -> bool:
    """
    Pre-flight check: verify that signing infrastructure is available.

    For PFX mode, checks that the file exists.  For token mode, checks that
    a smart-card device is present and (unless *certificate_auto_select* is
    used alone) that the specific certificate is in the Windows store.

    :param pfx_path: path to PFX certificate file (PFX mode)
    :param certificate_sha1: SHA1 thumbprint for cert store lookup (token mode)
    :param certificate_subject: subject name for cert store lookup (token mode)
    :param certificate_auto_select: True to auto-select certificate (token mode)
    :return: True if signing infrastructure appears available
    """
    if pfx_path is not None:
        if pfx_path.exists():
            return True
        log.warning(f"PFX certificate file does not exist: {pfx_path}")
        return False

    token_mode = certificate_sha1 is not None or certificate_subject is not None or certificate_auto_select
    if not token_mode:
        return False

    if is_rdp_session():
        pyship_print(
            "RDP session detected - hardware token signing is not supported over Remote Desktop. "
            "Token PIN entry does not work over RDP, and failed attempts may lock your token. "
            "Please sign from a local console session."
        )
        return False

    if not is_token_present():
        pyship_print("hardware token not detected — plug in your USB device")
        return False

    # For auto-select we can't check a specific cert, just confirm hardware is present
    if certificate_auto_select and certificate_sha1 is None and certificate_subject is None:
        return True

    if not is_certificate_in_store(certificate_sha1=certificate_sha1, certificate_subject=certificate_subject):
        pyship_print("certificate not found in Windows Certificate Store")
        return False

    return True


# ---------------------------------------------------------------------------
# Signing functions
# ---------------------------------------------------------------------------


@typechecked
def sign_file(file_path: Path, pfx_path: Path, certificate_password: str, timestamp_url: str, signtool_path: Union[Path, None] = None) -> bool:
    """
    Sign a file using signtool.exe with a PFX certificate.

    :param file_path: path to the file to sign
    :param pfx_path: path to the PFX certificate file
    :param certificate_password: password for the PFX certificate
    :param timestamp_url: RFC 3161 timestamp server URL
    :param signtool_path: explicit path to signtool.exe; auto-discovered if None
    :return: True if signing succeeded, False otherwise
    """
    signtool_path = _resolve_signtool(signtool_path)
    if signtool_path is None:
        return False

    if not file_path.exists():
        log.error(f"file to sign does not exist: {file_path}")
        return False
    if not pfx_path.exists():
        log.error(f"PFX certificate file does not exist: {pfx_path}")
        return False

    cmd = [str(signtool_path), "sign", "/f", str(pfx_path), "/p", certificate_password, "/tr", timestamp_url, "/td", "sha256", "/fd", "sha256", str(file_path)]
    return _run_signtool(cmd, file_path)


@typechecked
def sign_file_token(
    file_path: Path,
    timestamp_url: str,
    certificate_sha1: Union[str, None] = None,
    certificate_subject: Union[str, None] = None,
    certificate_auto_select: bool = False,
    token_pin: Union[str, None] = None,
    certificate_csp: Union[str, None] = None,
    certificate_key_container: Union[str, None] = None,
    signtool_path: Union[Path, None] = None,
) -> bool:
    """
    Sign a file using signtool.exe with a certificate from the Windows Certificate Store.

    Exactly one certificate selector (``certificate_sha1``, ``certificate_subject``,
    or ``certificate_auto_select``) must be provided.

    :param file_path: path to the file to sign
    :param timestamp_url: RFC 3161 timestamp server URL
    :param certificate_sha1: SHA1 thumbprint of certificate in the store
    :param certificate_subject: subject name of certificate in the store
    :param certificate_auto_select: use ``/a`` flag to auto-select best signing certificate
    :param token_pin: hardware token PIN (optional; token middleware may prompt interactively)
    :param certificate_csp: cryptographic service provider name (``/csp``)
    :param certificate_key_container: key container name (``/kc``)
    :param signtool_path: explicit path to signtool.exe; auto-discovered if None
    :return: True if signing succeeded, False otherwise
    """
    signtool_path = _resolve_signtool(signtool_path)
    if signtool_path is None:
        return False

    if not file_path.exists():
        log.error(f"file to sign does not exist: {file_path}")
        return False

    # Validate exactly one certificate selector is provided
    selectors = sum([certificate_sha1 is not None, certificate_subject is not None, certificate_auto_select])
    if selectors == 0:
        log.error("no certificate selector provided (need certificate_sha1, certificate_subject, or certificate_auto_select)")
        return False
    if selectors > 1:
        log.error("multiple certificate selectors provided; use only one of certificate_sha1, certificate_subject, or certificate_auto_select")
        return False

    # Build signtool command
    cmd = [str(signtool_path), "sign"]

    if certificate_sha1 is not None:
        clean_sha1 = _validate_sha1(certificate_sha1)
        if clean_sha1 is None:
            return False
        cmd.extend(["/sha1", clean_sha1])
    elif certificate_subject is not None:
        cmd.extend(["/n", certificate_subject])
    elif certificate_auto_select:
        cmd.append("/a")

    if certificate_csp is not None:
        cmd.extend(["/csp", certificate_csp])
    if certificate_key_container is not None:
        cmd.extend(["/kc", certificate_key_container])
    if token_pin is not None:
        cmd.extend(["/p", token_pin])

    cmd.extend(["/tr", timestamp_url, "/td", "sha256", "/fd", "sha256", str(file_path)])
    return _run_signtool(cmd, file_path)


@typechecked
def sign_if_configured(
    file_path: Union[Path, None],
    pfx_path: Union[Path, None],
    certificate_password: Union[str, None],
    timestamp_url: str,
    signtool_path: Union[Path, None] = None,
    certificate_sha1: Union[str, None] = None,
    certificate_subject: Union[str, None] = None,
    certificate_auto_select: bool = False,
    certificate_csp: Union[str, None] = None,
    certificate_key_container: Union[str, None] = None,
) -> bool:
    """
    Sign a file, dispatching to PFX or token mode based on which parameters are set.

    - **PFX mode** is active when *pfx_path* is not None.
    - **Token mode** is active when any of *certificate_sha1*, *certificate_subject*,
      or *certificate_auto_select* is set.
    - Setting both modes simultaneously is an error.
    - If neither mode is configured, signing is skipped with a warning.

    :param file_path: path to the file to sign, or None to skip
    :param pfx_path: path to the PFX certificate file, or None to skip
    :param certificate_password: PFX password or hardware token PIN, or None
    :param timestamp_url: RFC 3161 timestamp server URL
    :param signtool_path: explicit path to signtool.exe; auto-discovered if None
    :param certificate_sha1: SHA1 thumbprint of certificate in Windows Certificate Store
    :param certificate_subject: subject name of certificate in Windows Certificate Store
    :param certificate_auto_select: use ``/a`` flag to auto-select best signing certificate
    :param certificate_csp: cryptographic service provider name (``/csp``)
    :param certificate_key_container: key container name (``/kc``)
    :return: True if signing succeeded, False if skipped or failed
    """
    if file_path is None:
        log.debug("file_path is None; skipping signing")
        return False

    token_mode = certificate_sha1 is not None or certificate_subject is not None or certificate_auto_select
    pfx_mode = pfx_path is not None

    if pfx_mode and token_mode:
        log.error("both PFX and hardware token signing configured; use only one mode")
        return False

    if token_mode:
        if certificate_password is None:
            log.debug("token PIN not provided; hardware token may prompt for PIN interactively")
        return sign_file_token(
            file_path,
            timestamp_url,
            certificate_sha1=certificate_sha1,
            certificate_subject=certificate_subject,
            certificate_auto_select=certificate_auto_select,
            token_pin=certificate_password,
            certificate_csp=certificate_csp,
            certificate_key_container=certificate_key_container,
            signtool_path=signtool_path,
        )

    if pfx_mode:
        if certificate_password is None:
            log.warning("pfx_path is set but certificate_password not configured; skipping signing")
            return False
        return sign_file(file_path, pfx_path, certificate_password, timestamp_url, signtool_path)

    log.warning("no signing configuration provided; skipping signing")
    return False
