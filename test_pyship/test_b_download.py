import io
import sys
import tarfile
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from pyship.download import is_within_directory, safe_extract, extract


# --- is_within_directory ---


def test_is_within_directory_child_path(tmp_path):
    target = tmp_path / "sub" / "file.txt"
    assert is_within_directory(tmp_path, target) is True


def test_is_within_directory_same_path(tmp_path):
    assert is_within_directory(tmp_path, tmp_path) is True


def test_is_within_directory_sibling_path(tmp_path):
    sibling = tmp_path.parent / "other"
    assert is_within_directory(tmp_path, sibling) is False


def test_is_within_directory_parent_path(tmp_path):
    assert is_within_directory(tmp_path, tmp_path.parent) is False


def test_is_within_directory_absolute_traversal():
    base = Path("/base/dir")
    target = Path("/base/dir/sub/file.txt")
    assert is_within_directory(base, target) is True


def test_is_within_directory_traversal_attempt():
    base = Path("/base/dir")
    target = Path("/base/other")
    assert is_within_directory(base, target) is False


# --- safe_extract ---


def _make_tar_gz(content: bytes, member_name: str) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        info = tarfile.TarInfo(name=member_name)
        info.size = len(content)
        tf.addfile(info, io.BytesIO(content))
    return buf.getvalue()


def test_safe_extract_valid_archive(tmp_path):
    archive_path = tmp_path / "valid.tgz"
    archive_path.write_bytes(_make_tar_gz(b"hello content", "subdir/file.txt"))
    dest = tmp_path / "out"
    dest.mkdir()

    with tarfile.open(archive_path) as tf:
        safe_extract(tf, dest)

    assert (dest / "subdir" / "file.txt").exists()
    assert (dest / "subdir" / "file.txt").read_bytes() == b"hello content"


@pytest.mark.skipif(
    sys.version_info < (3, 14), reason="tarfile built-in path traversal filter enforced in Python 3.14+; safe_extract's own Windows check uses absolute() which doesn't resolve '..'"
)
def test_safe_extract_path_traversal_raises(tmp_path):
    archive_path = tmp_path / "evil.tgz"
    archive_path.write_bytes(_make_tar_gz(b"malicious", "../../../evil.txt"))
    dest = tmp_path / "out"
    dest.mkdir()

    # Python 3.14's tarfile enforces the 'data' filter by default, blocking
    # path traversal attempts with OutsideDestinationError.
    with tarfile.open(archive_path) as tf:
        with pytest.raises(Exception):
            safe_extract(tf, dest)


def test_safe_extract_multiple_files(tmp_path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, content in [("a.txt", b"aaa"), ("b.txt", b"bbb")]:
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tf.addfile(info, io.BytesIO(content))
    archive_path = tmp_path / "multi.tgz"
    archive_path.write_bytes(buf.getvalue())
    dest = tmp_path / "out"
    dest.mkdir()

    with tarfile.open(archive_path) as tf:
        safe_extract(tf, dest)

    assert (dest / "a.txt").read_bytes() == b"aaa"
    assert (dest / "b.txt").read_bytes() == b"bbb"


# --- extract ---


def test_extract_zip(tmp_path):
    archive_dir = tmp_path / "archives"
    archive_dir.mkdir()
    zip_path = archive_dir / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("hello.txt", "hello world")

    dest = tmp_path / "out"
    extract(archive_dir, Path("test.zip"), dest)

    assert (dest / "hello.txt").exists()
    assert (dest / "hello.txt").read_text() == "hello world"


def test_extract_tgz(tmp_path):
    archive_dir = tmp_path / "archives"
    archive_dir.mkdir()
    tgz_path = archive_dir / "test.tgz"
    tgz_path.write_bytes(_make_tar_gz(b"tgz content", "content.txt"))

    dest = tmp_path / "out"
    extract(archive_dir, Path("test.tgz"), dest)

    assert (dest / "content.txt").exists()
    assert (dest / "content.txt").read_bytes() == b"tgz content"


def test_extract_gz(tmp_path):
    archive_dir = tmp_path / "archives"
    archive_dir.mkdir()
    gz_path = archive_dir / "test.gz"
    gz_path.write_bytes(_make_tar_gz(b"gz content", "gz_file.txt"))

    dest = tmp_path / "out"
    extract(archive_dir, Path("test.gz"), dest)

    assert (dest / "gz_file.txt").exists()


def test_extract_unsupported_format_raises(tmp_path):
    archive_dir = tmp_path / "archives"
    archive_dir.mkdir()
    (archive_dir / "file.rar").write_bytes(b"fake rar content")

    dest = tmp_path / "out"
    with pytest.raises(Exception, match="Unsupported file type"):
        extract(archive_dir, Path("file.rar"), dest)


def test_extract_zip_multiple_files(tmp_path):
    archive_dir = tmp_path / "archives"
    archive_dir.mkdir()
    zip_path = archive_dir / "multi.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("file1.txt", "content1")
        zf.writestr("file2.txt", "content2")

    dest = tmp_path / "out"
    extract(archive_dir, Path("multi.zip"), dest)

    assert (dest / "file1.txt").read_text() == "content1"
    assert (dest / "file2.txt").read_text() == "content2"
