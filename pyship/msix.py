import re
import shutil
import struct
import zlib
from pathlib import Path
from typing import Union

from semver import VersionInfo
from typeguard import typechecked
from balsa import get_logger

from pyship import __application_name__, AppInfo, pyship_print, subprocess_run
from pyship.signing import _SDK_BIN_DIR

log = get_logger(__application_name__)

# Required Store logo asset filenames and their nominal sizes (for documentation).
_MSIX_ASSETS = ("StoreLogo.png", "Square44x44Logo.png", "Square150x150Logo.png")

_MANIFEST_TEMPLATE = """\
<?xml version="1.0" encoding="utf-8"?>
<Package xmlns="http://schemas.microsoft.com/appx/manifest/foundation/windows10"
         xmlns:uap="http://schemas.microsoft.com/appx/manifest/uap/windows10"
         xmlns:rescap="http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities">
  <Identity Name="{identity_name}"
            Publisher="{publisher}"
            Version="{version}"
            ProcessorArchitecture="x64" />
  <Properties>
    <DisplayName>{display_name}</DisplayName>
    <PublisherDisplayName>{publisher_display_name}</PublisherDisplayName>
    <Logo>assets/StoreLogo.png</Logo>
  </Properties>
  <Dependencies>
    <TargetDeviceFamily Name="Windows.Desktop" MinVersion="10.0.17763.0" MaxCompatibleVersion="10.0.99999.0" />
  </Dependencies>
  <Capabilities>
    <rescap:Capability Name="runFullTrust" />
  </Capabilities>
  <Applications>
    <Application Id="App"
                 Executable="{app_name}/{app_name}.exe"
                 EntryPoint="Windows.FullTrustApplication">
      <uap:VisualElements DisplayName="{display_name}"
                          Description="{description}"
                          BackgroundColor="transparent"
                          Square150x150Logo="assets/Square150x150Logo.png"
                          Square44x44Logo="assets/Square44x44Logo.png">
      </uap:VisualElements>
    </Application>
  </Applications>
</Package>
"""


@typechecked
def _find_makeappx(_sdk_bin_dir: Path = _SDK_BIN_DIR) -> Union[Path, None]:
    """
    Locate makeappx.exe from the Windows SDK bin directory.
    :param _sdk_bin_dir: Windows SDK bin directory to search
    :return: path to makeappx.exe with the highest SDK version, or None if not found
    """
    if not _sdk_bin_dir.is_dir():
        return None

    candidates = []
    for child in _sdk_bin_dir.iterdir():
        if child.is_dir() and child.name.startswith("10."):
            makeappx = Path(child, "x64", "makeappx.exe")
            if makeappx.exists():
                try:
                    version_tuple = tuple(int(x) for x in child.name.split("."))
                    candidates.append((version_tuple, makeappx))
                except ValueError:
                    pass

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0], reverse=True)
    return candidates[0][1]


@typechecked
def _msix_safe_name(s: str) -> str:
    """
    Sanitize a string for use in an MSIX Identity Name (alphanumeric, period, dash, underscore only).
    :param s: input string
    :return: sanitized string safe for MSIX Identity Name
    """
    safe = re.sub(r"[^A-Za-z0-9.\-_]", "-", s).strip(".")
    return safe or "App"


def _make_placeholder_png() -> bytes:
    """
    Return bytes of a minimal valid 1x1 white PNG using only stdlib (struct + zlib).
    Used when no store_assets_dir is provided.
    :return: PNG file bytes
    """

    def chunk(tag: bytes, data: bytes) -> bytes:
        body = tag + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))  # 1x1, 8-bit RGB
    idat = chunk(b"IDAT", zlib.compress(b"\x00\xff\xff\xff"))  # filter=none, white pixel
    iend = chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


@typechecked
def create_msix(
    target_app_info: AppInfo,
    app_dir: Path,
    msix_publisher: str,
    store_assets_dir: Union[Path, None] = None,
    makeappx_path: Union[Path, None] = None,
) -> Union[Path, None]:
    """
    Create an MSIX package from the pyship app directory.

    Writes AppxManifest.xml and assets/ into app_dir, then calls makeappx.exe to pack
    the directory into a .msix file. Run after run_nsis() so that MSIX-specific files
    added to app_dir do not affect the NSIS installer.

    :param target_app_info: target app info
    :param app_dir: app directory containing the launcher and CLIP subdirectory
    :param msix_publisher: certificate subject DN matching the signing cert exactly (e.g. "CN=My Co, O=My Co LLC, C=US")
    :param store_assets_dir: directory containing StoreLogo.png, Square44x44Logo.png, Square150x150Logo.png; placeholder 1x1 PNGs are used if None
    :param makeappx_path: explicit path to makeappx.exe; auto-discovered from Windows SDK if None
    :return: path to the .msix file on success, None if makeappx.exe is not found or packaging fails
    """
    assert isinstance(target_app_info.name, str)
    assert isinstance(target_app_info.author, str)
    assert isinstance(target_app_info.version, VersionInfo)

    if makeappx_path is None:
        makeappx_path = _find_makeappx()
    if makeappx_path is None:
        log.warning("makeappx.exe not found in Windows SDK; skipping MSIX creation")
        return None

    if target_app_info.run_on_startup:
        log.warning("run_on_startup=True is not supported in MSIX packages; startup behaviour must be configured via the StartupTask extension in a custom AppxManifest")

    # Write AppxManifest.xml into app_dir root
    identity_name = f"{_msix_safe_name(target_app_info.author)}.{_msix_safe_name(target_app_info.name)}"
    version_str = f"{target_app_info.version.major}.{target_app_info.version.minor}.{target_app_info.version.patch}.0"
    description = target_app_info.description or target_app_info.name
    manifest_content = _MANIFEST_TEMPLATE.format(
        identity_name=identity_name,
        publisher=msix_publisher,
        version=version_str,
        display_name=target_app_info.name,
        publisher_display_name=target_app_info.author,
        app_name=target_app_info.name,
        description=description,
    )
    manifest_path = Path(app_dir, "AppxManifest.xml")
    manifest_path.write_text(manifest_content, encoding="utf-8")
    log.info(f"wrote {manifest_path}")

    # Write assets into app_dir/assets/
    assets_dir = Path(app_dir, "assets")
    assets_dir.mkdir(exist_ok=True)
    placeholder = _make_placeholder_png()
    for asset_name in _MSIX_ASSETS:
        dest = Path(assets_dir, asset_name)
        if store_assets_dir is not None:
            src = Path(store_assets_dir, asset_name)
            if src.exists():
                shutil.copy2(str(src), str(dest))
                continue
            else:
                log.warning(f"store asset not found: {src}; using placeholder")
        dest.write_bytes(placeholder)

    # Pack with makeappx
    from pyshipupdate import get_target_os

    installers_dir = Path(target_app_info.project_dir, "installers")
    installers_dir.mkdir(parents=True, exist_ok=True)
    msix_path = Path(installers_dir, f"{target_app_info.name}_installer_{get_target_os()}.msix")

    cmd = [str(makeappx_path), "pack", "/d", str(app_dir), "/p", str(msix_path), "/o"]
    pyship_print(f'building MSIX package "{msix_path}"')
    return_code, _, _ = subprocess_run(cmd)

    if return_code == 0 and msix_path.exists():
        pyship_print(f'created MSIX "{msix_path}"')
        return msix_path
    else:
        log.error(f"makeappx returned exit code {return_code}")
        return None
