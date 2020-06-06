from dataclasses import dataclass
from pathlib import Path
from tempfile import mkdtemp
import shutil

import boto3
import boto3.s3
import boto3.exceptions
import semver

from pyship import get_logger, Updater, rmdir
from pyship import __application_name__ as pyship_application_name

log = get_logger(pyship_application_name)


@dataclass()
class UpdaterAwsS3(Updater):
    """
    pyship updater via AWS S3
    """

    target_app_name: str
    s3_bucket_name: str = None

    # if not provided, boto3 will try to determine these (see boto3's docs on where it looks)
    region_name: str = None
    aws_access_key_id: str = None
    aws_secret_access_key: str = None
    is_public_readable = bool = False

    def __init__(self):
        if self.s3_bucket_name is None:
            self.s3_bucket_name = f"{self.target_app_name}-{pyship_application_name}"  # S3 buckets can't have underscores, so use a dash
        super().__init__()

    def _get_s3_bucket(self):
        session = boto3.Session(region_name=self.region_name, aws_access_key_id=self.aws_access_key_id, aws_secret_access_key=self.aws_secret_access_key)
        s3_resource = session.resource("s3")
        return s3_resource.Bucket(self.s3_bucket_name)

    def _s3_bucket_exists(self, bucket):
        return bucket.creation_date is not None

    def get_available_versions(self) -> (list, None):
        versions = None
        try:
            s3_bucket = self._get_s3_bucket()
            versions = []
            for s3_object in s3_bucket.filter(Prefix=self.target_app_name):
                key = s3_object.key
                if key is not None and len(key) > 0:
                    key_split = key.split("_")  # todo: use a regex with the target app name so this is more robust
                    if len(key_split) > 1:
                        try:
                            versions.append(semver.VersionInfo.parse(key_split[-1]))
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
        return versions

    def push(self, pyshipy_dir: Path) -> bool:
        """
        push a pyshipy dir to S3
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
            if not self._s3_bucket_exists(s3_bucket):
                if self.is_public_readable:
                    acl = 'public-read'
                else:
                    acl = 'authenticated-read'
                s3_bucket.create(ACL=acl)

            # upload the pyshipy zip
            s3_bucket.upload_file(pyshipy_zip_file_path, pyshipy_zip_file_path.name)
            success = True

        except boto3.exceptions.Boto3Error as e:
            log.warning(f"{pyshipy_dir=} {e}")

        rmdir(temp_dir)

        return success
