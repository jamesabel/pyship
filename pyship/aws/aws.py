from dataclasses import dataclass
from pathlib import Path
import os
import time

from typeguard import typechecked
import boto3
import boto3.s3
import boto3.exceptions
from s3transfer import S3Transfer
from s3transfer.exceptions import S3UploadFailedError

from pyship import get_logger
from pyship import __application_name__ as pyship_application_name

log = get_logger(pyship_application_name)


@dataclass
class AWSAccess:
    resource_name: str
    profile_name: str = None
    region_name: str = None
    aws_access_key_id: str = None
    aws_secret_access_key: str = None

    @typechecked(always=True)
    def get_session(self):
        # use keys in AWS config
        # https://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html
        log.debug(f"{self.profile_name=}")
        return boto3.session.Session(profile_name=self.profile_name)

    @typechecked(always=True)
    def get_resource(self):
        if self.profile_name is None:
            resource = boto3.resource(self.resource_name)
        else:
            session = self.get_session(self.profile_name)
            resource = session.resource(self.resource_name)
        return resource

    @typechecked(always=True)
    def get_client(self):
        if self.profile_name is None:
            client = boto3.client(self.resource_name)
        else:
            session = self.get_session(self.profile_name)
            client = session.client(self.resource_name)
        return client


class AWSS3Access(AWSAccess):
    def __init__(self):
        super().__init__("s3")


@dataclass
class AWSS3Bucket(AWSS3Access):
    bucket_name: str = None

    @typechecked(always=True)
    def get_bucket(self, bucket_name: str):
        s3_resource = self.get_resource()
        return s3_resource.Bucket(bucket_name)

    @typechecked(always=True)
    def bucket_exists(self, bucket_resource) -> bool:
        return bucket_resource.creation_date is not None  # apparently the best way to determine if a bucket exists

    @typechecked(always=True)
    def object_exists(self, bucket_resource, key: str) -> bool:
        """
        determine if an S3 object exists
        :param bucket_resource: bucket resource
        :param key: object key
        :return: True if S3 object exists
        """
        objs = list(bucket_resource.objects.filter(Prefix=key))
        return len(objs) > 0 and objs[0].key == key

    @typechecked(always=True)
    def get_size_mtime_hash(self, s3_key: str) -> tuple:
        """
        get S3 object size, modification time and hash (AKA etag)
        :param s3_key: object key
        :return: tuple of size, modification time, hash (AWS etag)
        """
        bucket_resource = self.get_bucket(self.bucket_name)
        if self.object_exists(bucket_resource, s3_key):
            bucket_object = bucket_resource.Object(s3_key)
            object_size = bucket_object.content_length
            object_mtime = bucket_object.last_modified
            object_hash = bucket_object.e_tag[1:-1].lower()  # generally the file hash, but check the AWS docs for details on the etag
        else:
            object_size = None
            object_mtime = None
            object_hash = None  # does not exist
        log.debug(f"{self.bucket_name=},{s3_key=},{object_size=},{object_mtime=},{object_hash=}")
        return object_size, object_mtime, object_hash

    @typechecked(always=True)
    def upload(self, file_path: Path, s3_bucket: str, s3_key: str, force=False):
        """
        upload file to S3
        :param file_path: path to file to upload
        :param s3_bucket: S3 bucket
        :param s3_key: S3 key
        :param force: force upload (otherwise checks file size to determine if upload should happen)
        :return: True if upload successful
        """

        log.info(f"S3 upload : file_path={file_path} : bucket={s3_bucket} : key={s3_key}")

        uploaded_flag = False

        s3_size, _, s3_hash = self.get_size_mtime_hash(s3_bucket, s3_key)
        file_size = os.path.getsize(str(file_path))

        # if S3 hash is None, file does not exist
        # for zip files, usually the size changes if the contents change
        if force or s3_hash is None or file_size != s3_size:
            log.info(f"file size of local file is {file_size} and the S3 size is {s3_size}, force={force} - uploading")
            s3_client = self.get_client()
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
    def download(self, file_path: Path, s3_bucket: str, s3_key: str):
        """
        download a file from S3
        :param file_path: file path to write to
        :param s3_bucket: S3 bucket name
        :param s3_key: object key
        :param profile_name: AWS profile name
        """
        log.info(f"S3 download : {file_path=},{s3_bucket=},{s3_key=}")
        s3_client = self.get_client()
        transfer = S3Transfer(s3_client)
        transfer.download_file(s3_bucket, s3_key, file_path)
