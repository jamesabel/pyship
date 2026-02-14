# CLAUDE.md - Project Guide for pyship

## What is pyship?

pyship is a Windows application freezer, installer, and updater for Python applications. It creates a CLIP (Complete Location Independent Python) environment, a native launcher executable, and an NSIS installer. It optionally uploads artifacts to AWS S3 for distribution.

## Key Concepts

- **CLIP** - A standalone Python environment (copied from uv-managed python-build-standalone) containing the target app and all dependencies. Layout: `python.exe` at root, `Lib/site-packages/`.
- **Launcher** - A small C# stub `.exe` (compiled via `csc.exe`) plus a standalone Python script that finds and runs the latest CLIP version.
- **Target app** - The Python application being shipped.

## Project Structure

```
pyship/              # Main package
  launcher/          # Launcher subpackage (standalone script + C# stub)
  uv_util.py         # uv bootstrap, venv creation, pip install, wheel building
  clip.py            # CLIP creation (uses uv_util)
  pyship.py          # PyShip class with ship() orchestrator
  app_info.py        # AppInfo dataclass, metadata from pyproject.toml + wheel
  create_launcher.py # Compiles C# stub and copies standalone launcher script
  launcher_stub.py   # C# source template and csc.exe compilation
  nsis.py            # NSIS installer script generation
  cloud.py           # AWS S3 upload
  download.py        # File download with caching and safe extraction
test_pyship/         # Tests (alphabetically ordered: test_a_, test_b_, etc.)
  tstpyshipapp_0.0.1/  # Test application v0.0.1
  tstpyshipapp_0.0.2/  # Test application v0.0.2
scripts/             # Developer utilities (ruff, ty)
```

## Development Setup

```batch
uv venv venv
uv pip install --python venv\Scripts\python.exe -U setuptools
uv pip install --python venv\Scripts\python.exe -U -r requirements-dev.txt
```

Or run `make_venv.bat`.

## Building

```batch
build.bat
```

Builds a wheel into `dist/` using `python -m build --wheel`.

## Running Tests

```batch
venv\Scripts\python.exe -m pytest test_pyship/ -v
```

- Tests are ordered alphabetically by filename prefix (`test_a_`, `test_b_`, ..., `test_z_`).
- `conftest.py` has a session fixture that builds the pyship wheel and sets up an ERROR-level log handler that fails tests on any ERROR log message.
- `pyproject.toml` `[tool.pytest.ini_options]` excludes `tstpyshipapp` directories from recursive collection.
- Some tests (test_y, test_z) require the test app to have a venv set up.

## Code Conventions

- **Type checking**: All public functions use `@typechecked` from `typeguard` (v4, no parentheses). Use `Union[X, None]` for optional types.
- **Logging**: Each module does `log = get_logger(__application_name__)` via `balsa`. Use `pyship_print()` for user-facing messages (combines logging + timestamped console output).
- **Paths**: Use `pathlib.Path` exclusively, never `os.path`. `NullPath()` is used for uninitialized path fields.
- **Data classes**: `@dataclass` for simple containers (`AppInfo`), `@attrs(auto_attribs=True)` for richer classes (`PyShip`).
- **Docstrings**: Sphinx-style with `:param name:` and `:return:` tags.
- **Formatting**: Ruff format with line length 192. Ruff lint ignores E402, F401, E501. Type checking via ty.
- **Imports**: stdlib, then third-party, then local. `__init__.py` uses explicit relative imports for all public API exports.
- **Subprocess**: Use `subprocess_run()` wrapper from `pyship_subprocess.py` which clears PATH/PYTHONPATH for clean execution. For uv commands, use helpers in `uv_util.py`.

## Architecture Flow (PyShip.ship())

1. `get_app_info()` - Read pyproject.toml + inspect wheel for metadata
2. `create_pyship_launcher()` - Compile C# stub via csc.exe + copy standalone launcher script
3. `create_clip()` - Bootstrap uv, copy standalone Python, install target app
4. `create_clip_file()` - Zip the CLIP directory (with `.clip` extension)
5. `run_nsis()` - Generate and run NSIS installer script
6. Upload installer + clip to S3 (optional)

## Key Dependencies

| Package | Purpose |
|---------|---------|
| `pyshipupdate` | Sister package for app self-updates |
| `balsa` | Logging framework |
| `typeguard` | Runtime type checking (v2 API: `@typechecked`) |
| `semver` | Semantic version parsing |
| `toml` | Parse pyproject.toml |
| `wheel-inspect` | Extract metadata from .whl files |
| `awsimple` / `boto3` | AWS S3 uploads |
| `attrs` | Decorated classes |
| `requests` | HTTP downloads |

## Important Notes

- Windows-only currently. Paths and scripts assume Windows.
- The `pyshipupdate` package is a sibling project (not on PyPI); its wheel is expected at `../pyshipupdate/dist/` for local development.
- CLIP uses a standalone Python (from python-build-standalone via uv) so `python.exe` is at `<clip_dir>/python.exe`.
