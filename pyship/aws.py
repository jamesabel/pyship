from dataclasses import dataclass
from pathlib import Path

import boto3
import boto3.exceptions
import semver

from pyship import get_logger, __application_name__, Updater

log = get_logger(__application_name__)


@dataclass()
class UpdaterAwsS3(Updater):
    """
    pyship updater via AWS S3
    """

    s3_bucket_name: str
    target_app_name: str
    region: str = None
    aws_access_key_id: str = None
    aws_secret_access_key: str = None

    def _get_s3_resource(self):
        return boto3.resource("s3")

    def get_available_versions(self) -> (list, None):
        versions = None
        try:
            s3_resource = self._get_s3_resource()
            s3_bucket = s3_resource.Bucket(self.s3_bucket_name)
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
        success = False
        return success
