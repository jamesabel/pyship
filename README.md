# PyShip

[![CI](https://github.com/jamesabel/pyship/actions/workflows/ci.yml/badge.svg)](https://github.com/jamesabel/pyship/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/jamesabel/pyship/branch/main/graph/badge.svg)](https://codecov.io/gh/jamesabel/pyship)

Enables shipping a python application to end users.

## PyShip's Major Features

* Freeze practically any Python application
* Creates an installer
* Uploads application installer and updates to the cloud
* Automatic application updating in the background (no user intervention)
* OS native application (e.g. .exe for Windows)
* Run on OS startup option

## Documentation and Examples

[Learn PyShip By Example](https://github.com/jamesabel/pyshipexample)

[Short video on pyship given at Pyninsula](https://abelpublic.s3.us-west-2.amazonaws.com/pyship_pyninsula_10_2020.mkv)

## Configuration

pyship settings can be configured in your project's `pyproject.toml` under `[tool.pyship]`. Most settings can also be overridden via CLI arguments (CLI takes precedence).

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

### CLI Arguments

| Argument | pyproject.toml key | Description |
|----------|-------------------|-------------|
| `-p`, `--profile` | `profile` | AWS IAM profile for S3 uploads |
| `--noupload` | `upload` | Disable cloud upload (CLI flag inverts the toml boolean) |
| `--public-readable` | `public_readable` | Make uploaded S3 objects publicly readable |
| `-i`, `--id` | *(CLI only)* | AWS Access Key ID |
| `-s`, `--secret` | *(CLI only)* | AWS Secret Access Key |

`--id` and `--secret` are intentionally CLI-only since `pyproject.toml` is typically version-controlled.

## Code Signing

Signing your executables suppresses the Windows SmartScreen "Unknown Publisher" warning. pyship signs two files: the launcher stub (`{app_name}.exe`) and the NSIS installer (`{app_name}_installer_*.exe`). The launcher is signed before NSIS packages it, so the signed binary ends up inside the installer.

You need an Authenticode certificate in PFX format and signtool.exe from the Windows SDK.

### Getting signtool.exe

Install the [Windows SDK](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/) and select **Windows SDK Signing Tools for Desktop Apps**. pyship auto-discovers the newest version under `C:\Program Files (x86)\Windows Kits\10\bin\`.

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
    certificate_password_env_var="PFX_PASSWORD",   # reads os.environ["PFX_PASSWORD"] at ship() time
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
    signtool_path=Path(r"C:\custom\path\signtool.exe"),
)
```

### Timestamp server

By default pyship uses DigiCert's RFC 3161 server (`http://timestamp.digicert.com`). Override it with the `timestamp_url` field:

```python
ps = PyShip(
    ...
    timestamp_url="http://timestamp.sectigo.com",
)
```

### Verifying a signed executable

```batch
signtool verify /pa /v YourApp.exe
```

### Skipping signing

Leave `pfx_path` and `certificate_password` / `certificate_password_env_var` unset (the defaults). pyship will build and package the executables without signing them.

## Testing

Run tests with:

```batch
venv\Scripts\python.exe -m pytest test_pyship/ -v
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWSIMPLE_USE_MOTO_MOCK` | Set to `0` to use real AWS instead of [moto](https://github.com/getmoto/moto) mock. Required for `test_f_update` which tests cross-process S3 updates. Requires valid AWS credentials configured. | `1` (use moto) |
| `MAKE_NSIS_PATH` | Path to the NSIS `makensis.exe` executable. | `C:\Program Files (x86)\NSIS\makensis.exe` |

### Test Modes

- **Default (moto mock)**: All tests run with mocked AWS S3. No credentials needed. `test_f_update` is skipped.
- **Real AWS** (`AWSIMPLE_USE_MOTO_MOCK=0`): All tests run against real AWS S3. `test_f_update` runs and tests cross-process updates.
