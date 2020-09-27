from abc import ABC
from semver import VersionInfo
from pathlib import Path
import json
import time

from awsimple import S3Access

name_string = "name"
version_string = "version"
timestamp_string = "ts"  # timestamp is sometimes a keyword


class PyShipCloud(ABC):
    """
    base class for all cloud access
    """

    def __init__(self, app_name: str):
        self.app_name = app_name

    def get_latest_version(self) -> VersionInfo:
        """
        get the latest version of the target app
        :return: version as a VersionInfo object
        """
        ...

    def write_app_info(self, version: VersionInfo):
        """
        write all app info (particularly the latest version)
        :param version: version
        """
        ...

    def upload_lip_file(self, lip_file_path: Path):
        """
        upload the lip file to the cloud that can be used to update the target app
        :param lip_file_path: path to lip file (a zipped up lip dir)
        """
        ...

    def download_lip_file(self, lip_file_path: Path):
        """
        download the lip file, most likely to do an update to a new version
        :param lip_file_path: path to lip file (a zipped up lip dir)
        """
        ...


class PyShipAWS(PyShipCloud):
    """
    AWS cloud access
    """
    def __init__(self, app_name: str, s3_access: S3Access):
        """
        AWS cloud access
        :param app_name: target application name
        :param s3_access: instance of an S3Access class from awsimple
        """
        super().__init__(app_name)
        self.s3_access = s3_access
        self.app_info_s3_key = f"{self.app_name}.json"

    def get_latest_version(self) -> VersionInfo:
        app_info = json.loads(self.s3_access.read_string(self.app_info_s3_key))
        return app_info.get(version_string)

    def write_app_info(self, version: VersionInfo):
        app_info = {name_string: self.app_name, version_string: str(version), timestamp_string: time.time()}
        self.s3_access.write_string(json.dumps(app_info, indent=4), self.app_info_s3_key)

    def upload_lip_file(self, lip_file_path: Path):
        self.s3_access.upload(lip_file_path, lip_file_path.name)

    def download_lip_file(self, lip_file_path: Path):
        self.s3_access.download_cached(lip_file_path.name, lip_file_path)
