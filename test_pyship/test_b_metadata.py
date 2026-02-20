import json

from pyship.launcher.metadata import load_metadata, store_metadata


def test_store_then_load_roundtrip(tmp_path):
    data = {"key": "value", "num": 42, "nested": {"x": True}}
    store_metadata(tmp_path, "meta.json", data)
    loaded = load_metadata(tmp_path, "meta.json")
    assert loaded == data


def test_load_nonexistent_returns_none(tmp_path):
    result = load_metadata(tmp_path, "nonexistent.json")
    assert result is None


def test_store_creates_directory_if_missing(tmp_path):
    new_dir = tmp_path / "subdir"
    assert not new_dir.exists()
    store_metadata(new_dir, "meta.json", {"a": 1})
    assert new_dir.exists()
    assert (new_dir / "meta.json").exists()


def test_store_overwrites_existing(tmp_path):
    store_metadata(tmp_path, "meta.json", {"a": 1})
    store_metadata(tmp_path, "meta.json", {"b": 2})
    loaded = load_metadata(tmp_path, "meta.json")
    assert loaded == {"b": 2}
    assert "a" not in loaded


def test_stored_file_is_valid_json(tmp_path):
    data = {"key": "value"}
    store_metadata(tmp_path, "meta.json", data)
    with (tmp_path / "meta.json").open() as f:
        parsed = json.load(f)
    assert parsed == data


def test_store_empty_dict(tmp_path):
    store_metadata(tmp_path, "meta.json", {})
    loaded = load_metadata(tmp_path, "meta.json")
    assert loaded == {}


def test_store_multiple_files_in_same_dir(tmp_path):
    store_metadata(tmp_path, "a.json", {"a": 1})
    store_metadata(tmp_path, "b.json", {"b": 2})
    assert load_metadata(tmp_path, "a.json") == {"a": 1}
    assert load_metadata(tmp_path, "b.json") == {"b": 2}


def test_load_nonexistent_dir_returns_none(tmp_path):
    missing_dir = tmp_path / "no_such_dir"
    result = load_metadata(missing_dir, "meta.json")
    assert result is None


def test_store_with_string_values(tmp_path):
    data = {"app": "myapp", "version": "1.2.3", "author": "tester"}
    store_metadata(tmp_path, "meta.json", data)
    loaded = load_metadata(tmp_path, "meta.json")
    assert loaded["app"] == "myapp"
    assert loaded["version"] == "1.2.3"
    assert loaded["author"] == "tester"
