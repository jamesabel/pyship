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
from dataclasses import dataclass
from pathlib import Path
from typing import Union

if sys.platform == "win32":
    import ctypes

from typeguard import typechecked
from balsa import get_logger

from pyship import __application_name__
from pyship.custom_print import pyship_print
from pyship.subprocess import subprocess_run
from pyship.windows_sdk import WINDOWS_SDK_BIN_DIR, find_sdk_tool

log = get_logger(__application_name__)

_SDK_BIN_DIR = WINDOWS_SDK_BIN_DIR  # backwards-compatible alias

#: User-facing message shown when hardware-token signing is blocked by an RDP session.
RDP_SIGNING_BLOCKED_MESSAGE = (
    "RDP session detected - hardware token signing is not supported over Remote Desktop. "
    "Token PIN entry does not work over RDP, and failed attempts may lock your token. "
    "Please sign from a local console session."
)

#: Default RFC 3161 timestamp server.
DEFAULT_TIMESTAMP_URL = "http://timestamp.digicert.com"


@dataclass
class SigningConfig:
    """
    Everything needed to sign an executable, in one place.

    Two mutually exclusive modes:

    - **PFX mode** (:attr:`pfx_mode`): active when :attr:`pfx_path` is set;
      :attr:`certificate_password` is the PFX password (required to sign).
    - **Token mode** (:attr:`token_mode`): active when any of
      :attr:`certificate_sha1`, :attr:`certificate_subject`, or
      :attr:`certificate_auto_select` is set; :attr:`certificate_password` is
      the optional token PIN (the token middleware may prompt interactively).
    """

    pfx_path: Union[Path, None] = None  # PFX certificate file (PFX mode)
    certificate_password: Union[str, None] = None  # PFX password or hardware token PIN
    timestamp_url: str = DEFAULT_TIMESTAMP_URL  # RFC 3161 timestamp server URL
    signtool_path: Union[Path, None] = None  # explicit signtool.exe; auto-discovered if None
    certificate_sha1: Union[str, None] = None  # SHA1 thumbprint in Windows Certificate Store (token mode, /sha1)
    certificate_subject: Union[str, None] = None  # certificate subject name (token mode, /n)
    certificate_auto_select: bool = False  # auto-select best signing certificate (token mode, /a)
    certificate_csp: Union[str, None] = None  # cryptographic service provider (token mode, /csp)
    certificate_key_container: Union[str, None] = None  # key container name (token mode, /kc)

    @property
    def pfx_mode(self) -> bool:
        """True when PFX-file signing is configured."""
        return self.pfx_path is not None

    @property
    def token_mode(self) -> bool:
        """True when any hardware-token certificate selector is configured."""
        return self.certificate_sha1 is not None or self.certificate_subject is not None or self.certificate_auto_select


# ---------------------------------------------------------------------------
# Internal helpers (shared by PFX and token signing)
# ---------------------------------------------------------------------------


@typechecked
def _find_signtool(_sdk_bin_dir: Path = WINDOWS_SDK_BIN_DIR) -> Union[Path, None]:
    """
    Locate signtool.exe from the Windows SDK bin directory.

    :param _sdk_bin_dir: Windows SDK bin directory to search
    :return: path to signtool.exe from the highest SDK version, or None if not found
    """
    return find_sdk_tool("signtool.exe", _sdk_bin_dir)


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
def check_signing_available(config: SigningConfig) -> bool:
    """
    Pre-flight check: verify that signing infrastructure is available.

    For PFX mode, checks that the file exists.  For token mode, checks that
    the session is not RDP, a smart-card device is present, and (unless
    auto-select is used alone) that the specific certificate is in the
    Windows store.

    :param config: signing configuration
    :return: True if signing infrastructure appears available
    """
    if config.pfx_path is not None:
        if config.pfx_path.exists():
            return True
        log.warning(f"PFX certificate file does not exist: {config.pfx_path}")
        return False

    if not config.token_mode:
        return False

    if is_rdp_session():
        pyship_print(RDP_SIGNING_BLOCKED_MESSAGE)
        return False

    if not is_token_present():
        pyship_print("hardware token not detected — plug in your USB device")
        return False

    # For auto-select we can't check a specific cert, just confirm hardware is present
    if config.certificate_auto_select and config.certificate_sha1 is None and config.certificate_subject is None:
        return True

    if not is_certificate_in_store(certificate_sha1=config.certificate_sha1, certificate_subject=config.certificate_subject):
        pyship_print("certificate not found in Windows Certificate Store")
        return False

    return True


# ---------------------------------------------------------------------------
# Signing functions
# ---------------------------------------------------------------------------


@typechecked
def sign_file(file_path: Path, config: SigningConfig) -> bool:
    """
    Sign a file using signtool.exe with a PFX certificate.

    Requires ``config.pfx_path`` and ``config.certificate_password`` to be set.

    :param file_path: path to the file to sign
    :param config: signing configuration (PFX mode)
    :return: True if signing succeeded, False otherwise
    """
    signtool_path = _resolve_signtool(config.signtool_path)
    if signtool_path is None:
        return False

    if not file_path.exists():
        log.error(f"file to sign does not exist: {file_path}")
        return False
    if config.pfx_path is None or not config.pfx_path.exists():
        log.error(f"PFX certificate file does not exist: {config.pfx_path}")
        return False
    if config.certificate_password is None:
        log.error("PFX mode requires certificate_password")
        return False

    cmd = [str(signtool_path), "sign", "/f", str(config.pfx_path), "/p", config.certificate_password, "/tr", config.timestamp_url, "/td", "sha256", "/fd", "sha256", str(file_path)]
    return _run_signtool(cmd, file_path)


@typechecked
def sign_file_token(file_path: Path, config: SigningConfig) -> bool:
    """
    Sign a file using signtool.exe with a certificate from the Windows Certificate Store.

    Exactly one certificate selector (``certificate_sha1``, ``certificate_subject``,
    or ``certificate_auto_select``) must be set in *config*.
    ``config.certificate_password`` is used as the token PIN if provided;
    otherwise the token middleware may prompt interactively.

    :param file_path: path to the file to sign
    :param config: signing configuration (token mode)
    :return: True if signing succeeded, False otherwise
    """
    signtool_path = _resolve_signtool(config.signtool_path)
    if signtool_path is None:
        return False

    if not file_path.exists():
        log.error(f"file to sign does not exist: {file_path}")
        return False

    # Validate exactly one certificate selector is provided
    selectors = sum([config.certificate_sha1 is not None, config.certificate_subject is not None, config.certificate_auto_select])
    if selectors == 0:
        log.error("no certificate selector provided (need certificate_sha1, certificate_subject, or certificate_auto_select)")
        return False
    if selectors > 1:
        log.error("multiple certificate selectors provided; use only one of certificate_sha1, certificate_subject, or certificate_auto_select")
        return False

    # Build signtool command
    cmd = [str(signtool_path), "sign"]

    if config.certificate_sha1 is not None:
        clean_sha1 = _validate_sha1(config.certificate_sha1)
        if clean_sha1 is None:
            return False
        cmd.extend(["/sha1", clean_sha1])
    elif config.certificate_subject is not None:
        cmd.extend(["/n", config.certificate_subject])
    elif config.certificate_auto_select:
        cmd.append("/a")

    if config.certificate_csp is not None:
        cmd.extend(["/csp", config.certificate_csp])
    if config.certificate_key_container is not None:
        cmd.extend(["/kc", config.certificate_key_container])
    if config.certificate_password is not None:
        cmd.extend(["/p", config.certificate_password])

    cmd.extend(["/tr", config.timestamp_url, "/td", "sha256", "/fd", "sha256", str(file_path)])
    return _run_signtool(cmd, file_path)


@typechecked
def sign_if_configured(file_path: Union[Path, None], config: SigningConfig) -> bool:
    """
    Sign a file, dispatching to PFX or token mode based on the configuration.

    - **PFX mode** is active when ``config.pfx_path`` is set.
    - **Token mode** is active when any hardware-token certificate selector is set.
    - Configuring both modes simultaneously is an error.
    - If neither mode is configured, signing is skipped with a warning.

    :param file_path: path to the file to sign, or None to skip
    :param config: signing configuration
    :return: True if signing succeeded, False if skipped or failed
    """
    if file_path is None:
        log.debug("file_path is None; skipping signing")
        return False

    if config.pfx_mode and config.token_mode:
        log.error("both PFX and hardware token signing configured; use only one mode")
        return False

    if config.token_mode:
        if config.certificate_password is None:
            log.debug("token PIN not provided; hardware token may prompt for PIN interactively")
        return sign_file_token(file_path, config)

    if config.pfx_mode:
        if config.certificate_password is None:
            log.warning("pfx_path is set but certificate_password not configured; skipping signing")
            return False
        return sign_file(file_path, config)

    log.warning("no signing configuration provided; skipping signing")
    return False
