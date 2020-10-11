from semver import VersionInfo

from pyship import version_from_clip_zip


def test_version_from_pyshipy():
    target_app_name = "abc"
    for target_app_version in ["10.23.38", "0.0.1", "345.0.1-dev", "1.0.0-alpha.1"]:
        for extension in ["zip", "7z"]:
            pyshipy_zip_string = f"{target_app_name}_{target_app_version}.{extension}"
            version = version_from_clip_zip(target_app_name, pyshipy_zip_string)
            assert version == VersionInfo.parse(target_app_version)

    # various strings with no or illegal version
    assert version_from_clip_zip(target_app_name, "") is None
    assert version_from_clip_zip(target_app_name, ".zip") is None
    assert version_from_clip_zip(target_app_name, "©_1.2.3.zip") is None  # unicode
    assert version_from_clip_zip(target_app_name, "xyzzy.zip") is None
    assert version_from_clip_zip(target_app_name, "xyzzy_.zip") is None
    assert version_from_clip_zip(target_app_name, "a_1.x.2.7z") is None
    assert version_from_clip_zip(target_app_name, target_app_name) is None
    assert version_from_clip_zip(target_app_name, f"{target_app_name}_") is None
    assert version_from_clip_zip(target_app_name, f"{target_app_name}_0") is None
    assert version_from_clip_zip(target_app_name, f"{target_app_name}_1.2") is None
