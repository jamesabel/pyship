# this is from sundry. todo: separate this out into its own package/module on PyPI

import hashlib


def _get_string_hash(s, hash_function):
    hash_object = hash_function()
    hash_object.update(s.encode())
    hash_str = hash_object.hexdigest().lower()
    return hash_str


def get_string_md5(s):
    return _get_string_hash(s, hashlib.md5)


def get_string_sha256(s):
    return _get_string_hash(s, hashlib.sha256)


def get_string_sha512(s):
    return _get_string_hash(s, hashlib.sha512)


def get_file_md5(file_path):
    return _get_file_hash(file_path, hashlib.md5)


def get_file_sha256(file_path):
    return _get_file_hash(file_path, hashlib.sha256)


def get_file_sha512(file_path):
    return _get_file_hash(file_path, hashlib.sha512)


def _get_file_hash(file_path, hash_function):
    hash_object = hash_function()

    bucket_size = 4096  # for speed
    f = open(file_path, "rb")
    val = f.read(bucket_size)
    while len(val) > 0:
        hash_object.update(val)
        val = f.read(bucket_size)
    f.close()

    hash_str = hash_object.hexdigest().lower()

    return hash_str
