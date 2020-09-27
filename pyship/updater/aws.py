from dataclasses import dataclass
from pathlib import Path
from tempfile import mkdtemp
import shutil
import semver

from typeguard import typechecked
import boto3
import boto3.exceptions

from pyship import get_logger, rmdir
from pyship import __application_name__ as pyship_application_name
from pyship.updater import Updater
from pyship.aws import AWSS3Bucket

log = get_logger(pyship_application_name)


@dataclass
class UpdaterAwsS3(AWSS3Bucket, Updater):
    """
    pyship updater via AWS S3
    """

    s3_bucket_name: str = None

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
    def push(self, lip_dir: Path) -> bool:
        """
        push a lip dir up to S3
        :param lip_dir: lip dir (name is <app>_<version>)
        :return: True on success, False otherwise
        """

        success = False

        # zip the lip dir
        temp_dir = mkdtemp()
        lip_zip_file_path = shutil.make_archive(Path(temp_dir, lip_dir.name), "zip", str(lip_dir))

        try:
            s3_bucket = self._get_s3_bucket()

            # create the S3 bucket if it doesn't exist
            if not aws_s3_bucket_exists(s3_bucket):
                if self.is_public_readable:
                    acl = "public-read"
                else:
                    acl = "authenticated-read"
                s3_bucket.create(ACL=acl)

            # upload the lip zip
            s3_bucket.upload_file(lip_zip_file_path, lip_zip_file_path.name)
            success = True

        except boto3.exceptions.Boto3Error as e:
            log.warning(f"{lip_dir=} {e}")

        rmdir(temp_dir)

        return success
