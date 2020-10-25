from semver import VersionInfo
from pathlib import Path
import json
import time

from typeguard import typechecked
from awsimple import S3Access

name_string = "name"
version_string = "version"
timestamp_string = "ts"  # timestamp is sometimes a keyword


class PyShipCloud:
    """
    AWS cloud access
    """

    def __init__(self, app_name: str, s3_access: S3Access):
        """
        AWS cloud access
        :param app_name: target application name
        :param s3_access: instance of an S3Access class from awsimple
        """
        self.app_name = app_name
        self.s3_access = s3_access
        self.app_info_s3_key = f"{self.app_name}.json"

    @typechecked
    def get_latest_version(self) -> VersionInfo:
        app_info = json.loads(self.s3_access.read_string(self.app_info_s3_key))
        return app_info.get(version_string)

    @typechecked
    def write_app_info(self, version: VersionInfo):
        app_info = {name_string: self.app_name, version_string: str(version), timestamp_string: time.time()}
        self.s3_access.write_string(json.dumps(app_info, indent=4), self.app_info_s3_key)

    @typechecked
    def upload(self, file_path: Path):
        self.s3_access.upload(file_path, file_path.name)

    @typechecked
    def download(self, file_path: Path):
        self.s3_access.download_cached(file_path.name, file_path)
