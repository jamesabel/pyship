import hashlib

from pyship.launcher.hash import (
    get_string_md5,
    get_string_sha256,
    get_string_sha512,
    get_file_md5,
    get_file_sha256,
    get_file_sha512,
)

# Pre-computed expected hashes for "hello"
HELLO_MD5 = "5d41402abc4b2a76b9719d911017c592"
HELLO_SHA256 = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
HELLO_SHA512 = "9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca72323c3d99ba5c11d7c7acc6e14b8c5da0c4663475c2e5c3adef46f73bcdec043"


# --- String hash tests ---


def test_get_string_md5_known_value():
    assert get_string_md5("hello") == HELLO_MD5


def test_get_string_sha256_known_value():
    assert get_string_sha256("hello") == HELLO_SHA256


def test_get_string_sha512_known_value():
    assert get_string_sha512("hello") == HELLO_SHA512


def test_string_hash_is_lowercase():
    result = get_string_md5("UPPER")
    assert result == result.lower()


def test_string_sha256_is_lowercase():
    result = get_string_sha256("UPPER")
    assert result == result.lower()


def test_string_hash_empty_string_md5():
    result = get_string_md5("")
    assert result == hashlib.md5(b"").hexdigest()


def test_string_hash_empty_string_sha256():
    result = get_string_sha256("")
    assert result == hashlib.sha256(b"").hexdigest()


def test_string_hash_deterministic():
    assert get_string_sha256("same input") == get_string_sha256("same input")


def test_string_hash_different_inputs_differ():
    assert get_string_sha256("hello") != get_string_sha256("world")


# --- File hash tests ---


def test_get_file_md5_known_value(tmp_path):
    p = tmp_path / "test.txt"
    p.write_bytes(b"hello")
    assert get_file_md5(p) == HELLO_MD5


def test_get_file_sha256_known_value(tmp_path):
    p = tmp_path / "test.txt"
    p.write_bytes(b"hello")
    assert get_file_sha256(p) == HELLO_SHA256


def test_get_file_sha512_known_value(tmp_path):
    p = tmp_path / "test.txt"
    p.write_bytes(b"hello")
    assert get_file_sha512(p) == HELLO_SHA512


def test_file_hash_is_lowercase(tmp_path):
    p = tmp_path / "test.txt"
    p.write_bytes(b"UPPER")
    result = get_file_sha256(p)
    assert result == result.lower()


def test_file_hash_large_file_beyond_bucket_size(tmp_path):
    """Files larger than the 4096-byte read bucket are hashed correctly."""
    p = tmp_path / "large.bin"
    data = b"x" * 10000
    p.write_bytes(data)
    expected = hashlib.sha256(data).hexdigest()
    assert get_file_sha256(p) == expected


def test_file_hash_empty_file(tmp_path):
    p = tmp_path / "empty.txt"
    p.write_bytes(b"")
    assert get_file_sha256(p) == hashlib.sha256(b"").hexdigest()


def test_string_vs_file_hash_match(tmp_path):
    """String and file hashes match for identical content."""
    content = "consistent content"
    p = tmp_path / "content.txt"
    p.write_bytes(content.encode())
    assert get_string_sha256(content) == get_file_sha256(p)


def test_file_hashes_differ_for_different_content(tmp_path):
    p1 = tmp_path / "a.txt"
    p2 = tmp_path / "b.txt"
    p1.write_bytes(b"aaa")
    p2.write_bytes(b"bbb")
    assert get_file_sha256(p1) != get_file_sha256(p2)
