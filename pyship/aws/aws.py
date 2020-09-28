# from pathlib import Path
# import os
# import time
# from abc import ABC
#
# from typeguard import typechecked
# import boto3
# import boto3.s3
# import boto3.exceptions
# from s3transfer import S3Transfer
# from s3transfer.exceptions import S3UploadFailedError
#
# from pyship import get_logger
# from pyship import __application_name__ as pyship_application_name
#
# log = get_logger(pyship_application_name)
#
#
# class AWSAccess(ABC):
#
#     def __init__(self, resource_name: str, profile_name: str = None, region_name: str = None, aws_access_key_id: str = None, aws_secret_access_key: str = None):
#         self.resource_name = resource_name
#         self.profile_name = profile_name
#         self.region_name = region_name
#         self.aws_access_key_id = aws_access_key_id
#         self.aws_secret_access_key = aws_secret_access_key
#
#         self.session = None
#
#     def get_session(self):
#         # use keys in AWS config
#         # https://docs.aws.amazon.com/cli/latest/userguide/cli-config-files.html
#         log.debug(f"{self.resource_name=},{self.profile_name=}")
#         self.session = boto3.session.Session(profile_name=self.profile_name, region_name=self.region_name, aws_access_key_id=self.aws_access_key_id,
#                                              aws_secret_access_key=self.aws_secret_access_key)
#
#     def get_resource(self):
#         if self.profile_name is None:
#             resource = boto3.resource(self.resource_name)
#         else:
#             resource = self.session.resource(self.resource_name)
#         return resource
#
#     def get_client(self):
#         if self.profile_name is None:
#             client = boto3.client(self.resource_name)
#         else:
#             client = self.session.client(self.resource_name)
#         return client
#
#
# class AWSS3Access(AWSAccess):
#     def __init__(self):
#         super().__init__("s3")
#
#
# class AWSS3Bucket(AWSS3Access):
#
#     def __init__(self, bucket_name: str):
#         super().__init__()
#         self.bucket_name = bucket_name
#         self.resource = self.get_resource()
#         self.bucket = self.resource.Bucket(self.bucket_name)
#         self.recommended_limit = 100  # we get all objects when we do a "dir", so it's suggested to keep the number of versions to a reasonable limit (user can override this)
#
#     def bucket_exists(self) -> bool:
#         return self.bucket.creation_date is not None  # apparently the best way to determine if a bucket exists
#
#     @typechecked(always=True)
#     def object_exists(self, key: str) -> bool:
#         """
#         determine if an S3 object exists
#         :param key: object key
#         :return: True if S3 object exists
#         """
#         objs = list(self.bucket.objects.filter(Prefix=key))
#         return len(objs) > 0 and objs[0].key == key
#
#     def dir(self) -> dict:
#         # returns a dict of ObjectSummary's (dict key is object key)
#         # https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#objectsummary
#         dir_results = {o.key: o for o in self.bucket.objects.all()}
#         number_of_entries = len(dir_results)
#         if number_of_entries > self.recommended_limit:
#             log.warning(f"{self.bucket_name=} has {number_of_entries} entries, which is above the recommended number")
#         return dir_results
#
#     @typechecked(always=True)
#     def get_size_mtime_hash(self, s3_key: str) -> tuple:
#         """
#         get S3 object size, modification time and hash (AKA etag)
#         :param s3_key: object key
#         :return: tuple of size, modification time, hash (AWS etag)
#         """
#
#         if self.object_exists(s3_key):
#             bucket_object = self.bucket.Object(s3_key)
#             object_size = bucket_object.content_length
#             object_mtime = bucket_object.last_modified
#             object_hash = bucket_object.e_tag[1:-1].lower()  # generally the file hash, but check the AWS docs for details on the etag
#         else:
#             object_size = None
#             object_mtime = None
#             object_hash = None  # does not exist
#         log.debug(f"{self.bucket_name=},{s3_key=},{object_size=},{object_mtime=},{object_hash=}")
#         return object_size, object_mtime, object_hash
#
#     @typechecked(always=True)
#     def upload(self, file_path: Path, force=False):
#         """
#         upload file to S3
#         :param file_path: path to file to upload
#         :param force: force upload (otherwise checks file size to determine if upload should happen)
#         :return: True if upload successful
#         """
#
#         s3_key = file_path.name
#         log.info(f"S3 upload : file_path={file_path} : bucket={self.bucket_name} : key={s3_key}")
#
#         uploaded_flag = False
#
#         s3_size, _, s3_hash = self.get_size_mtime_hash(s3_key)
#         file_size = os.path.getsize(str(file_path))
#
#         # if S3 hash is None, file does not exist
#         # for zip files, usually the size changes if the contents change
#         if force or s3_hash is None or file_size != s3_size:
#             log.info(f"file size of local file is {file_size} and the S3 size is {s3_size}, force={force} - uploading")
#             transfer = S3Transfer(self.get_client())
#
#             transfer_retry_count = 0
#             while not uploaded_flag and transfer_retry_count < 10:
#                 try:
#                     transfer.upload_file(file_path, self.bucket_name, s3_key)
#                     uploaded_flag = True
#                 except S3UploadFailedError as e:
#                     log.error(f"{file_path} to {self.bucket_name}:{s3_key} : {transfer_retry_count} : {e}")
#                     transfer_retry_count += 1
#                     time.sleep(1.0)
#
#         else:
#             log.info(f"file size of {file_size} is the same as is already on S3 and force={force} - not uploading")
#
#         return uploaded_flag
#
#     @typechecked(always=True)
#     def download(self, file_path: Path, s3_key: str):
#         """
#         download a file from S3
#         :param file_path: file path to write to
#         :param s3_key: S3 object key
#         """
#         log.info(f"S3 download : {file_path=},{self.bucket_name=},{s3_key=}")
#         transfer = S3Transfer(self.get_client())
#         transfer.download_file(self.bucket_name, s3_key, str(file_path))
