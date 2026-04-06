"""
PyShip orchestrator — the ``ship()`` method drives the full build-sign-package-upload pipeline.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Union

import platformdirs
from attr import attrs
from typeguard import typechecked
from awsimple import S3Access
from balsa import get_logger
from semver import VersionInfo

from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
from pyship import __version__ as pyship_version
from pyship import run_nsis, create_clip, create_pyship_launcher, pyship_print, APP_DIR_NAME, create_clip_file, get_app_info, PyShipCloud
from pyship.signing import sign_if_configured, check_signing_available, is_rdp_session
from pyship.msix import create_msix
from pyship import PyshipNoAppName
from pyship.exceptions import PyshipSigningUnavailable
from pyshipupdate import mkdirs, create_bucket_name
from pyshipupdate import __version__ as pyshipupdate_version

log = get_logger(pyship_application_name)

#: Environment variable pyship reads for the PFX password / hardware-token PIN.
SIGNING_PIN_ENV_VAR = "PYSHIP_SIGNING_CERTIFICATE_PIN"


@attrs(auto_attribs=True)
class PyShip:
    """
    Top-level class that drives the pyship pipeline.

    Instantiate with the desired configuration, then call :meth:`ship` to
    build, sign, package, and (optionally) upload the application.
    """

    # --- project paths ---
    project_dir: Path = Path()  # target app project dir (defaults to cwd)
    dist_dir: Path = Path("dist")  # wheel destination directory

    # --- cloud ---
    cloud_bucket: Union[str, None] = None
    cloud_profile: Union[str, None] = None
    cloud_id: Union[str, None] = None
    cloud_secret: Union[str, None] = None
    cloud_access: Union[PyShipCloud, None] = None
    name: Union[str, None] = None  # optional target application name (overrides pyproject.toml)
    upload: bool = True
    public_readable: bool = False

    # --- build ---
    python_version: Union[str, None] = None  # e.g. "3.12"; defaults to running Python's major.minor

    # --- code signing (common) ---
    code_sign: bool = False  # master switch: True → sign executables; failure aborts ship()
    certificate_password: Union[str, None] = None  # PFX password or hardware token PIN
    timestamp_url: str = "http://timestamp.digicert.com"  # RFC 3161 timestamp server
    signtool_path: Union[Path, None] = None  # explicit signtool.exe; auto-discovered if None

    # --- code signing (PFX mode) ---
    pfx_path: Union[Path, None] = None  # path to PFX certificate file

    # --- code signing (hardware-token mode) ---
    certificate_sha1: Union[str, None] = None  # SHA1 thumbprint in Windows Certificate Store
    certificate_subject: Union[str, None] = None  # certificate subject name (/n)
    certificate_auto_select: bool = False  # signtool /a
    certificate_csp: Union[str, None] = None  # cryptographic service provider (/csp)
    certificate_key_container: Union[str, None] = None  # key container name (/kc)

    # --- MSIX ---
    msix: bool = False
    msix_publisher: Union[str, None] = None  # certificate subject DN for MSIX Identity/@Publisher
    store_assets_dir: Union[Path, None] = None  # directory with Store logo PNGs
    makeappx_path: Union[Path, None] = None  # explicit makeappx.exe; auto-discovered if None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_password(self) -> Union[str, None]:
        """
        Resolve the signing password/PIN.
        Explicit ``certificate_password`` takes priority; falls back to the
        ``PYSHIP_SIGNING_CERTIFICATE_PIN`` environment variable.
        """
        if self.certificate_password is not None:
            return self.certificate_password
        return os.environ.get(SIGNING_PIN_ENV_VAR)

    def _sign_or_raise(self, file_path: Union[Path, None], effective_password: Union[str, None]) -> None:
        """
        Sign *file_path* using the configured mode.  Raises
        :class:`PyshipSigningUnavailable` on failure.

        Only called when ``self.code_sign`` is True.

        :param file_path: path to the executable to sign
        :param effective_password: resolved PFX password or token PIN
        """
        signed = sign_if_configured(
            file_path,
            self.pfx_path,
            effective_password,
            self.timestamp_url,
            self.signtool_path,
            certificate_sha1=self.certificate_sha1,
            certificate_subject=self.certificate_subject,
            certificate_auto_select=self.certificate_auto_select,
            certificate_csp=self.certificate_csp,
            certificate_key_container=self.certificate_key_container,
        )
        if not signed:
            raise PyshipSigningUnavailable(f"failed to sign {file_path}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @typechecked
    def ship(self) -> Union[Path, None]:
        """
        Perform all steps to ship the app: build, sign, package, and optionally upload.

        :return: path to the created installer, or None if the installer could
                 not be created (e.g. NSIS not available in CI)
        :raises PyshipSigningUnavailable: when ``code_sign`` is True and signing
                 infrastructure is missing or a file fails to sign
        """

        start_time = datetime.now()
        pyship_print(f"{pyship_application_name} starting (pyship={str(pyship_version)},pyshipupdate={str(pyshipupdate_version)},upload={self.upload},public_readable={self.public_readable})")

        # Clean dist directory to avoid stale wheels (multiple wheels cause metadata extraction to fail)
        dist_dir = Path(self.project_dir, self.dist_dir)
        if dist_dir.exists():
            mkdirs(dist_dir, remove_first=True)

        cache_dir = Path(platformdirs.user_cache_dir(pyship_application_name, pyship_author))

        effective_password = self._resolve_password()

        # Pre-flight signing check
        if self.code_sign:
            token_mode = self.certificate_sha1 is not None or self.certificate_subject is not None or self.certificate_auto_select
            if token_mode and is_rdp_session():
                pyship_print(
                    "RDP session detected - hardware token signing is not supported over Remote Desktop. "
                    "Token PIN entry does not work over RDP, and failed attempts may lock your token. "
                    "Please sign from a local console session."
                )
                return None
            available = check_signing_available(
                pfx_path=self.pfx_path,
                certificate_sha1=self.certificate_sha1,
                certificate_subject=self.certificate_subject,
                certificate_auto_select=self.certificate_auto_select,
            )
            if not available:
                raise PyshipSigningUnavailable("code_sign is True but signing infrastructure is not available")

        target_app_info = get_app_info(self.project_dir, Path(self.project_dir, self.dist_dir), cache_dir)

        if target_app_info.name is None:
            raise PyshipNoAppName
        else:
            app_dir = Path(self.project_dir, APP_DIR_NAME, target_app_info.name).absolute()

            mkdirs(app_dir, remove_first=True)

            launcher_exe_path = create_pyship_launcher(target_app_info, app_dir)
            if self.code_sign:
                self._sign_or_raise(launcher_exe_path, effective_password)

            clip_dir = create_clip(target_app_info, app_dir, Path(self.project_dir, self.dist_dir), cache_dir, python_version=self.python_version)

            clip_file_path = create_clip_file(clip_dir)
            assert isinstance(target_app_info.version, VersionInfo)
            installer_exe_path = run_nsis(target_app_info, target_app_info.version, app_dir)
            if installer_exe_path is not None and self.code_sign:
                self._sign_or_raise(installer_exe_path, effective_password)

            if self.msix:
                if self.msix_publisher is None:
                    log.error("msix=True but msix_publisher is not set; skipping MSIX creation")
                else:
                    msix_path = create_msix(target_app_info, app_dir, self.msix_publisher, self.store_assets_dir, self.makeappx_path)
                    if msix_path is not None and self.code_sign:
                        self._sign_or_raise(msix_path, effective_password)

            if self.upload and installer_exe_path is not None:
                if self.cloud_profile is None and self.cloud_id is None:
                    pyship_print("no cloud access provided - will not attempt upload")
                else:
                    assert isinstance(target_app_info.name, str)
                    assert isinstance(target_app_info.author, str)
                    bucket = create_bucket_name(target_app_info.name, target_app_info.author) if self.cloud_bucket is None else self.cloud_bucket

                    if self.cloud_profile is None:
                        if self.cloud_secret is None:
                            log.error(f"{self.cloud_secret=}")
                            s3_access = None
                        else:
                            s3_access = S3Access(bucket, aws_access_key_id=self.cloud_id, aws_secret_access_key=self.cloud_secret)
                    else:
                        s3_access = S3Access(bucket, profile_name=self.cloud_profile)

                    if s3_access is not None:
                        s3_access.public_readable = self.public_readable
                        self.cloud_access = PyShipCloud(target_app_info.name, s3_access)

                        installer_url = self.cloud_access.upload(installer_exe_path)
                        pyship_print(f'uploaded "{installer_exe_path}" to {installer_url}')

                        clip_url = self.cloud_access.upload(clip_file_path)
                        pyship_print(f'uploaded "{clip_file_path}" to {clip_url}')

            elif not self.upload:
                pyship_print("no upload requested")
            else:
                pyship_print("installer not created (NSIS not available) - skipping upload")

            elapsed_time = datetime.now() - start_time
            pyship_print(f"{pyship_application_name} done (elapsed_time={str(elapsed_time)})")

        return installer_exe_path
