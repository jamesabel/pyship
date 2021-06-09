from pathlib import Path

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

    @typechecked
    def upload(self, file_path: Path) -> str:
        """
        upload a file to S3 and return the URL
        :param file_path: path to the file to be uploaded
        :return: URL of uploaded file
        """
        s3_key = file_path.name
        self.s3_access.set_public_readable(True)  # all uploads are public readable (disable upload to keep installers and clips private)
        self.s3_access.create_bucket()
        self.s3_access.upload(file_path, s3_key)
        return self.s3_access.get_s3_object_url(s3_key)

    @typechecked
    def download(self, file_path: Path):
        self.s3_access.download_cached(file_path.name, file_path)
