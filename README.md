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

# Build settings
dist = "dist"            # directory containing the wheel (default: "dist")

# Cloud upload settings
profile = "default"      # AWS IAM profile for S3 uploads
upload = true            # upload installer and clip to S3 (default: true)
public_readable = false  # make uploaded S3 objects publicly readable (default: false)
```

### CLI Arguments

| Argument | pyproject.toml key | Description |
|----------|-------------------|-------------|
| `-p`, `--profile` | `profile` | AWS IAM profile for S3 uploads |
| `-d`, `--dist` | `dist` | Distribution directory containing the wheel |
| `--noupload` | `upload` | Disable cloud upload (CLI flag inverts the toml boolean) |
| `--public-readable` | `public_readable` | Make uploaded S3 objects publicly readable |
| `-i`, `--id` | *(CLI only)* | AWS Access Key ID |
| `-s`, `--secret` | *(CLI only)* | AWS Secret Access Key |

`--id` and `--secret` are intentionally CLI-only since `pyproject.toml` is typically version-controlled.

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
