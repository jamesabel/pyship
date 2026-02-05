# PyShip

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
