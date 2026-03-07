import pytest
from semver import VersionInfo

from pyship.app_info import _pep440_to_semver


@pytest.mark.parametrize(
    "pep440, expected_semver",
    [
        ("0.6.0", "0.6.0"),
        ("1.2.3", "1.2.3"),
        ("0.6.0a0", "0.6.0-alpha.0"),
        ("0.6.0a1", "0.6.0-alpha.1"),
        ("0.6.0b0", "0.6.0-beta.0"),
        ("0.6.0b2", "0.6.0-beta.2"),
        ("0.6.0rc0", "0.6.0-rc.0"),
        ("0.6.0rc1", "0.6.0-rc.1"),
        ("0.6.0.dev0", "0.6.0-dev.0"),
        ("0.6.0.dev3", "0.6.0-dev.3"),
    ],
)
def test_pep440_to_semver_conversion(pep440, expected_semver):
    assert _pep440_to_semver(pep440) == expected_semver


@pytest.mark.parametrize(
    "pep440",
    ["0.6.0a0", "0.6.0b1", "0.6.0rc0", "0.6.0.dev0", "0.6.0"],
)
def test_pep440_to_semver_parses_successfully(pep440):
    semver_str = _pep440_to_semver(pep440)
    v = VersionInfo.parse(semver_str)
    assert v.major == 0
    assert v.minor == 6
    assert v.patch == 0
