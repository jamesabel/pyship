from dataclasses import dataclass
from pathlib import Path
from tempfile import mkdtemp
import shutil
import os
import time

from typeguard import typechecked
import boto3
import boto3.s3
import boto3.exceptions
import semver
from s3transfer import S3Transfer
from s3transfer.exceptions import S3UploadFailedError

from pyship import get_logger, rmdir, Updater
from pyship import __application_name__ as pyship_application_name

log = get_logger(pyship_application_name)


@dataclass
class UpdaterAwsS3(Updater):
    """
    pyship updater via AWS S3
    """

    s3_bucket_name: str = None

    # if not provided, boto3 will try to determine these (see boto3's docs on where it looks)
    region_name: str = None
    aws_access_key_id: str = None
    aws_secret_access_key: str = None
    is_public_readable = bool = False

    def _get_s3_bucket(self):
        if self.s3_bucket_name is None:
            self.s3_bucket_name = f"{self.target_app_name}-{pyship_application_name}"  # S3 buckets can't have underscores, so use a dash
        session = boto3.Session(region_name=self.region_name, aws_access_key_id=self.aws_access_key_id, aws_secret_access_key=self.aws_secret_access_key)
        s3_resource = session.resource("s3")
        return s3_resource.Bucket(self.s3_bucket_name)

    def get_available_versions(self):
        available_versions = set()
        try:
            s3_bucket = self._get_s3_bucket()
            for s3_object in s3_bucket.filter(Prefix=self.target_app_name):
                key = s3_object.key
                if key is not None and len(key) > 0:
                    key_split = key.split("_")  # todo: use a regex with the target app name so this is more robust
                    if len(key_split) > 1:
                        try:
                            available_versions.add(semver.VersionInfo.parse(key_split[-1]))
                        except IndexError as e:
                            log.info(f"{key} {e}")
                        except TypeError as e:
                            log.info(f"{key} {e}")
                        except ValueError as e:
                            log.info(f"{key} {e}")
                    else:
                        log.info(f"{key=}")
                else:
                    log.info(f"{key=}")
        except boto3.exceptions.Boto3Error as e:
            log.info(e)
        return available_versions

    @typechecked(always=True)
    def push(self, pyshipy_dir: Path) -> bool:
        """
        push a pyshipy dir up to S3
        :param pyshipy_dir: pyshipy dir (name is <app>_<version>)
        :return: True on success, False otherwise
        """

        success = False

        # zip the pyshipy dir
        temp_dir = mkdtemp()
        pyshipy_zip_file_path = shutil.make_archive(Path(temp_dir, pyshipy_dir.name), "zip", str(pyshipy_dir))

        try:
            s3_bucket = self._get_s3_bucket()

            # create the S3 bucket if it doesn't exist
            if not aws_s3_bucket_exists(s3_bucket):
                if self.is_public_readable:
                    acl = "public-read"
                else:
                    acl = "authenticated-read"
                s3_bucket.create(ACL=acl)

            # upload the pyshipy zip
            s3_bucket.upload_file(pyshipy_zip_file_path, pyshipy_zip_file_path.name)
            success = True

        except boto3.exceptions.Boto3Error as e:
            log.warning(f"{pyshipy_dir=} {e}")

        rmdir(temp_dir)

        return success


@typechecked(always=True)
def _aws_get_session(profile_name: str):
    # use keys in AWS config
    # https://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html
    log.debug(f"{profile_name=}")
    return boto3.session.Session(profile_name=profile_name)


@typechecked(always=True)
def aws_get_s3_resource(profile_name: (str, None)):
    if profile_name is None:
        s3_resource = boto3.resource("s3")
    else:
        session = _aws_get_session(profile_name)
        s3_resource = session.resource("s3")
    return s3_resource


@typechecked(always=True)
def aws_get_s3_client(profile_name: (str, None)):
    if profile_name is None:
        s3_client = boto3.client("s3")
    else:
        session = _aws_get_session(profile_name)
        s3_client = session.client("s3")
    return s3_client


@typechecked(always=True)
def aws_get_s3_bucket(bucket_name: str, profile_name: (str, None)):
    s3_resource = aws_get_s3_resource(profile_name)
    return s3_resource.Bucket(bucket_name)


@typechecked(always=True)
def aws_s3_bucket_exists(bucket_resource) -> bool:
    return bucket_resource.creation_date is not None  # apparently the best way to determine if a bucket exists


@typechecked(always=True)
def aws_s3_object_exists(bucket_resource, key: str) -> bool:
    """
    determine if an S3 object exists
    :param bucket_resource: bucket resource
    :param key: object key
    :return: True if S3 object exists
    """
    objs = list(bucket_resource.objects.filter(Prefix=key))
    return len(objs) > 0 and objs[0].key == key


@typechecked(always=True)
def aws_s3_upload(file_path: Path, s3_bucket: str, s3_key: str, profile_name: (str, None), force=False):
    """
    upload file to S3
    :param file_path: path to file to upload
    :param s3_bucket: S3 bucket
    :param s3_key: S3 key
    :param profile_name: AWS profile to use
    :param force: force upload (otherwise checks file size to determine if upload should happen)
    :return: True if upload successful
    """

    log.info(f"S3 upload : file_path={file_path} : bucket={s3_bucket} : key={s3_key}")

    uploaded_flag = False

    s3_size, _, s3_hash = aws_s3_get_size_mtime_hash(s3_bucket, s3_key, profile_name)
    file_size = os.path.getsize(str(file_path))

    # if S3 hash is None, file does not exist
    # for zip files, usually the size changes if the contents change
    if force or s3_hash is None or file_size != s3_size:
        log.info(f"file size of local file is {file_size} and the S3 size is {s3_size}, force={force} - uploading")
        s3_client = aws_get_s3_client(profile_name)
        transfer = S3Transfer(s3_client)

        transfer_retry_count = 0
        while not uploaded_flag and transfer_retry_count < 10:
            try:
                transfer.upload_file(file_path, s3_bucket, s3_key)
                uploaded_flag = True
            except S3UploadFailedError as e:
                log.error(f"{file_path} to {s3_bucket}:{s3_key} : {transfer_retry_count} : {e}")
                transfer_retry_count += 1
                time.sleep(1.0)

    else:
        log.info(f"file size of {file_size} is the same as is already on S3 and force={force} - not uploading")

    return uploaded_flag


@typechecked(always=True)
def aws_s3_download(file_path: Path, s3_bucket: str, s3_key: str, profile_name: (str, None)):
    """
    download a file from S3
    :param file_path: file path to write to
    :param s3_bucket: S3 bucket name
    :param s3_key: object key
    :param profile_name: AWS profile name
    """
    log.info(f"S3 download : {file_path=},{s3_bucket=},{s3_key=}")
    s3_client = aws_get_s3_client(profile_name)
    transfer = S3Transfer(s3_client)
    transfer.download_file(s3_bucket, s3_key, file_path)


@typechecked(always=True)
def aws_s3_get_size_mtime_hash(s3_bucket_name: str, s3_key: str, profile_name: (str, None)) -> tuple:
    """
    get S3 object size, modification time and hash (AKA etag)
    :param s3_bucket_name: S3 bucket name
    :param s3_key: object key
    :param profile_name: AWS profile Name
    :return: tuple of size, modification time, hash (AWS etag)
    """
    bucket_resource = aws_get_s3_bucket(s3_bucket_name, profile_name)
    if aws_s3_object_exists(bucket_resource, s3_key, profile_name):
        bucket_object = bucket_resource.Object(s3_key)
        object_size = bucket_object.content_length
        object_mtime = bucket_object.last_modified
        object_hash = bucket_object.e_tag[1:-1].lower()  # generally the file hash, but check the AWS docs for details on the etag
    else:
        object_size = None
        object_mtime = None
        object_hash = None  # does not exist
    log.debug(f"{s3_bucket_name=},{s3_key=},{profile_name=},{object_size=},{object_mtime=},{object_hash=}")
    return object_size, object_mtime, object_hash
