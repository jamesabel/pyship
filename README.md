# PyShip

[![CI](https://github.com/jamesabel/pyship/actions/workflows/ci.yml/badge.svg)](https://github.com/jamesabel/pyship/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jamesabel/pyship/branch/main/graph/badge.svg)](https://codecov.io/gh/jamesabel/pyship)

Enables shipping a python application to end users.

## PyShip's Major Features

* Freeze practically any Python application.
* Optional Code Signing (avoid Windows "Unknown Publisher" warning). This is not required, and you can ship your
  application for free, but code signing is supported if you have a Code Signing certificate (typically an additional
  cost).
* Installs via Microsoft Windows App Store or self-hosted installers entirely outside the app store.
* Automatic application updating in the background (no user intervention).
* OS native application (e.g., .exe for Windows).
* Run on OS startup option.

Currently only for Windows. May be extended to other Operating Systems in the future.

## Configuration

pyship settings are configured in your project's `pyproject.toml` under `[tool.pyship]`.

### pyproject.toml

```toml
[tool.pyship]
# App metadata
is_gui = false           # true if the app is a GUI application (default: false)
run_on_startup = false   # true to run the app on OS startup (default: false)

# Cloud upload settings
profile = "default"      # AWS IAM profile for S3 uploads
upload = true            # upload installer and clip to S3 (default: true)
public_readable = false  # make uploaded S3 objects publicly readable (default: false)
```

### AWS Keys in CLI Arguments

The user may optionally provide their AWS keys as CLI arguments. They may also be provided in the `~/.aws/credentials`
file (typical for AWS CLI and boto3). These are not in `pyproject.toml` since it is usually checked into the code repo.

| Argument         | Description           |
|------------------|-----------------------|
| `-i`, `--id`     | AWS Access Key ID     |
| `-s`, `--secret` | AWS Secret Access Key |

## Microsoft Windows Code Signing (Optional)

Signing your executables suppresses the Windows SmartScreen "Unknown Publisher" warning. pyship signs two files: the
launcher stub (`{app_name}.exe`) and the NSIS installer (`{app_name}_installer_*.exe`). The launcher is signed before
NSIS packages it, so the signed binary ends up inside the installer.

You need an Authenticode code-signing certificate in PFX format, a password for that PFX file, and signtool.exe from
the Windows SDK.

### Getting a code-signing certificate

An Authenticode certificate identifies you (or your organisation) as the publisher of the software. Windows uses it to
suppress SmartScreen warnings and to display your name in UAC prompts and Add/Remove Programs.

**Certificate types**

| Type                         | SmartScreen behaviour                                                                             | Typical cost | Notes                                                                                                  |
|------------------------------|---------------------------------------------------------------------------------------------------|--------------|--------------------------------------------------------------------------------------------------------|
| OV (Organisation Validation) | Builds reputation over time; new certs still trigger SmartScreen until enough installs accumulate | ~$200–400/yr | Issued to a verified company or individual. Most common for open-source and small commercial projects. |
| EV (Extended Validation)     | Immediate SmartScreen reputation from the first install                                           | ~$400–600/yr | Requires a hardware token (USB) or cloud HSM. Strongest trust signal.                                  |

Self-signed certificates work for local development and testing but will **not** suppress SmartScreen and are rejected
by the Microsoft Store.

**Where to buy**

***tldr:***

[Sectigo Code Signing Certificate for ~$300-400/year](https://www.ssl2buy.com/sectigo-code-signing-certificate.php)

***Other options***

Certificates are issued by Certificate Authorities (CAs). Common options include:

- **SSL.com** — offers OV and EV code-signing certificates; EV certificates can be stored on their cloud-based eSigner
  HSM, making them usable in CI without a physical USB token.
- **DigiCert** — popular for EV certificates; offers KeyLocker (cloud HSM) for CI integration.
- **Sectigo (formerly Comodo)** — widely used OV and EV code-signing certificates.
- **SignPath** — free certificates for open-source projects via their Foundation programme.

The purchase process typically involves:

1. Choose a CA and certificate type (OV or EV).
2. Complete identity verification (business registration documents for OV; additional legal vetting for EV).
3. The CA issues a `.pfx` (PKCS #12) file containing your private key and certificate chain, or provides access via a
   hardware token / cloud HSM.

Verification usually takes 1–5 business days for OV, and 1–2 weeks for EV.

### The PFX file and password

The `.pfx` file (also called `.p12`) is an encrypted archive that bundles your private signing key with the certificate.
The **PFX password** (also called the export password) protects this file — anyone with both the file and the password
can sign software as you.

**Creating a PFX from separate files**

If your CA provided a `.crt` certificate and a `.key` private key separately (common with some CAs), combine them into
a PFX:

```batch
openssl pkcs12 -export -out certificate.pfx -inkey private.key -in certificate.crt -certfile ca_chain.crt
```

OpenSSL will prompt you to set a password — this becomes your PFX password.

**Extracting certificate info from a PFX**

To view the certificate subject (needed for `msix_publisher`):

```batch
certutil -dump certificate.pfx
```

**Security best practices**

- Never commit the `.pfx` file to your source repository. Add `*.pfx` to `.gitignore`.
- Store the PFX password in a secrets manager or CI secrets — not in source code, environment files, or scripts.
- For CI, base64-encode the PFX file and store it as a CI secret, then decode it at build time:
  ```yaml
  - name: Decode signing certificate
    run: echo "${{ secrets.PFX_BASE64 }}" | base64 --decode > certificate.pfx
  - name: Ship
    env:
      PFX_PASSWORD: ${{ secrets.PFX_PASSWORD }}
    run: python ship.py
  ```
- Rotate certificates before expiry. Most code-signing certificates are valid for 1–3 years.

### Getting signtool.exe

Install the [Windows SDK](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/) and select **Windows SDK
Signing Tools for Desktop Apps**. pyship auto-discovers the newest version under
`C:\Program Files (x86)\Windows Kits\10\bin\`.

### Basic usage

```python
from pathlib import Path
from pyship import PyShip

ps = PyShip(
    project_dir=Path("path/to/your/app"),
    pfx_path=Path("path/to/certificate.pfx"),
    certificate_password="your-pfx-password",
)
ps.ship()
```

### CI / environment variable password

Avoid storing the PFX password in source code. Pass it via an environment variable instead:

```python
ps = PyShip(
    project_dir=Path("path/to/your/app"),
    pfx_path=Path("path/to/certificate.pfx"),
    certificate_password_env_var="PFX_PASSWORD",  # reads os.environ["PFX_PASSWORD"] at ship() time
)
ps.ship()
```

Set the secret in your CI system (e.g. GitHub Actions → Settings → Secrets) and expose it in your workflow:

```yaml
- name: Ship
  env:
    PFX_PASSWORD: ${{ secrets.PFX_PASSWORD }}
  run: python ship.py
```

### Explicit signtool path

If signtool.exe is not in the default Windows SDK location, point pyship directly at it:

```python
ps = PyShip(
    ...
signtool_path = Path(r"C:\custom\path\signtool.exe"),
)
```

### Timestamp server

By default pyship uses DigiCert's RFC 3161 server (`http://timestamp.digicert.com`). Override it with the
`timestamp_url` field:

```python
ps = PyShip(
    ...
timestamp_url = "http://timestamp.sectigo.com",
)
```

### Verifying a signed executable

```batch
signtool verify /pa /v YourApp.exe
```

### Skipping signing

Leave `pfx_path` and `certificate_password` / `certificate_password_env_var` unset (the defaults). pyship will build and
package the executables without signing them.

## Microsoft Store Distribution (MSIX) (Optional)

The Microsoft Store is an alternative distribution channel that gives users a trusted, one-click install experience and
eliminates SmartScreen warnings entirely. pyship can produce both a traditional NSIS installer **and** an MSIX package
in a single `ship()` call.

### Prerequisites

| Requirement                      | Notes                                                                                                                                                                                                                                                                               |
|----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Windows SDK                      | Provides `makeappx.exe` and `signtool.exe`. Install from [developer.microsoft.com/windows/downloads/windows-sdk](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/) and select **Windows SDK Signing Tools for Desktop Apps**. pyship auto-discovers both tools. |
| Authenticode certificate         | Same PFX used for code signing. The `Publisher` field in the MSIX manifest must exactly match the certificate subject. Self-signed certificates work for sideloading and testing but not for Store submission.                                                                      |
| Microsoft Partner Center account | Required for Store submission only. Register at [partner.microsoft.com](https://partner.microsoft.com/). One-time $19 fee for individuals.                                                                                                                                          |

### Basic usage

Set `msix=True` and supply the certificate subject DN as `msix_publisher`:

```python
from pathlib import Path
from pyship import PyShip

ps = PyShip(
    project_dir=Path("path/to/your/app"),
    pfx_path=Path("certificate.pfx"),
    certificate_password_env_var="PFX_PASSWORD",
    msix=True,
    msix_publisher="CN=My Company, O=My Company LLC, C=US",  # must match cert subject exactly
)
ps.ship()
```

This produces two files in `installers/`:

- `{app_name}_installer_win.exe` — the NSIS installer (direct distribution, auto-updates via pyshipupdate)
- `{app_name}_installer_win.msix` — the MSIX package (Store or sideloading, updates managed by the Store)

Both are signed with the same certificate. The NSIS installer is built first; the MSIX is packed from the same app
directory afterwards, so they do not interfere with each other.

### Finding the msix_publisher string

`msix_publisher` must be the exact Distinguished Name of your signing certificate's subject. To read it from your PFX:

```batch
certutil -dump certificate.pfx
```

Look for the `Subject:` line, e.g. `CN=My Company, O=My Company LLC, C=US`. Copy it verbatim — any difference will cause
installation to fail.

### Store logo assets

MSIX packages require three PNG logo files. pyship generates 1×1 white placeholder PNGs automatically, which is
sufficient for testing and sideloading. For Store submission, provide real assets at the correct sizes:

| File                    | Size    |
|-------------------------|---------|
| `StoreLogo.png`         | 50×50   |
| `Square44x44Logo.png`   | 44×44   |
| `Square150x150Logo.png` | 150×150 |

Point pyship at a directory containing these files with `store_assets_dir`:

```python
ps = PyShip(
    ...
msix = True,
msix_publisher = "CN=My Company, O=My Company LLC, C=US",
store_assets_dir = Path("store_assets"),
)
```

Any asset not found in that directory falls back to the placeholder PNG automatically.

### Explicit makeappx path

If `makeappx.exe` is not in the default Windows SDK location:

```python
ps = PyShip(
    ...
makeappx_path = Path(r"C:\custom\path\makeappx.exe"),
)
```

### Sideloading (without the Store)

Signed MSIX packages can be installed directly without going through the Store — double-click the `.msix` file or use:

```batch
Add-AppxPackage -Path "{app_name}_installer_win.msix"
```

This is useful for enterprise deployments and beta distribution.

### Submitting to the Microsoft Store

1. Log in to [Partner Center](https://partner.microsoft.com/dashboard).
2. Go to **Windows & Xbox** → **Overview** → **Create a new app** and reserve your app name.
3. Under **Submissions** → **New submission**, complete the store listing (description, screenshots, age rating,
   pricing).
4. Upload your signed `.msix` from the `installers/` directory under **Packages**.
5. Submit for certification. Review typically takes 1–3 business days.

### Limitations

- `run_on_startup = true` is not supported in MSIX builds. The MSIX runtime requires a `StartupTask` extension in the
  manifest; pyship logs a warning and continues, but the app will not auto-start. Configure startup behaviour manually
  in a custom manifest if needed.
- MSIX packages installed via the Store are updated by the Store, not by pyshipupdate. The self-update logic in
  pyshipupdate is silently inactive when running inside an MSIX container.

### NSIS vs. MSIX comparison

|                 | NSIS installer          | MSIX                           |
|-----------------|-------------------------|--------------------------------|
| Distribution    | Your own URL / S3       | Microsoft Store or sideload    |
| SmartScreen     | Suppressed with EV cert | Not shown (implicitly trusted) |
| Auto-update     | pyshipupdate            | Store manages updates          |
| Review required | No                      | Yes (Store only; ~1–3 days)    |
| Revenue share   | None                    | 15% (>$1M/yr: 12%)             |
| Startup support | Yes                     | Requires manifest extension    |

## Testing

Run tests with:

```batch
venv\Scripts\python.exe -m pytest test_pyship/ -v
```

### Environment Variables

| Variable                 | Description                                                                                                                                                                                       | Default                                    |
|--------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------|
| `AWSIMPLE_USE_MOTO_MOCK` | Set to `0` to use real AWS instead of [moto](https://github.com/getmoto/moto) mock. Required for `test_f_update` which tests cross-process S3 updates. Requires valid AWS credentials configured. | `1` (use moto)                             |
| `MAKE_NSIS_PATH`         | Path to the NSIS `makensis.exe` executable.                                                                                                                                                       | `C:\Program Files (x86)\NSIS\makensis.exe` |

### Test Modes

- **Default (moto mock)**: All tests run with mocked AWS S3. No credentials needed. `test_f_update` is skipped.
- **Real AWS** (`AWSIMPLE_USE_MOTO_MOCK=0`): All tests run against real AWS S3. `test_f_update` runs and tests
  cross-process updates.
