import os


def is_ci() -> bool:
    """Check if running in a CI environment (GitHub Actions, etc.)."""
    return os.environ.get("CI", "").lower() == "true" or os.environ.get("GITHUB_ACTIONS", "").lower() == "true"
