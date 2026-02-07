from pathlib import Path
from datetime import datetime
from typing import Union

import platformdirs
from attr import attrs
from typeguard import typechecked
from awsimple import S3Access
from balsa import get_logger
from semver import VersionInfo

from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
from pyship import __version__ as pyship_version
from pyship import run_nsis, create_clip, create_pyship_launcher, pyship_print, APP_DIR_NAME, create_clip_file, DEFAULT_DIST_DIR_NAME, get_app_info, PyShipCloud
from pyship import PyshipNoProductDirectory, PyshipNoAppName, PyshipNoTargetAppInfo
from pyshipupdate import mkdirs, create_bucket_name
from pyshipupdate import __version__ as pyshipupdate_version

log = get_logger(pyship_application_name)


@attrs(auto_attribs=True)
class PyShip:
    project_dir: Path = Path()  # target app project dir, e.g. the "home" directory of the project.  If not set, current working directory is used.
    dist_dir: Path = Path(DEFAULT_DIST_DIR_NAME)  # many packaging tools (e.g filt, etc.) use "dist" as the package destination directory

    # cloud credentials, locations, etc.
    cloud_bucket: Union[str, None] = None  # e.g. AWS S3 bucket
    cloud_profile: Union[str, None] = None  # e.g. AWS IAM profile
    cloud_id: Union[str, None] = None  # e.g. AWS Access Key ID
    cloud_secret: Union[str, None] = None  # e.g. AWS Secret Access Key
    cloud_access: Union[PyShipCloud, None] = None  # making this accessible outside this class aids in testing, especially when mocking
    name: Union[str, None] = None  # optional target application name (overrides pyproject.toml)
    upload: bool = True  # set to False in order to tell pyship to not attempt to perform file upload to the cloud (e.g. installer, clip files to AWS S3)
    public_readable: bool = False  # set to True to make uploaded S3 objects publicly readable (sets ACL=public-read)

    @typechecked
    def ship(self) -> Union[Path, None]:
        """
        Perform all the steps to ship the app, including creating the installer.
        :return: the path to the created installer, or None if installer could not be created (e.g. NSIS not available in CI)
        """

        start_time = datetime.now()
        pyship_print(f"{pyship_application_name} starting (pyship={str(pyship_version)},pyshipupdate={str(pyshipupdate_version)},upload={self.upload},public_readable={self.public_readable})")

        cache_dir = Path(platformdirs.user_cache_dir(pyship_application_name, pyship_author))
        target_app_info = get_app_info(self.project_dir, self.dist_dir, cache_dir)

        if self.project_dir is None:
            assert isinstance(self.project_dir, Path)
            raise PyshipNoProductDirectory(self.project_dir)
        elif target_app_info is None:
            raise PyshipNoTargetAppInfo
        elif target_app_info.name is None:
            raise PyshipNoAppName
        else:
            app_dir = Path(self.project_dir, APP_DIR_NAME, target_app_info.name).absolute()

            mkdirs(app_dir, remove_first=True)

            create_pyship_launcher(target_app_info, app_dir)  # create the OS specific launcher executable

            clip_dir = create_clip(target_app_info, app_dir, Path(self.project_dir, self.dist_dir), cache_dir)

            clip_file_path = create_clip_file(clip_dir)  # create clip file
            assert isinstance(target_app_info.version, VersionInfo)
            installer_exe_path = run_nsis(target_app_info, target_app_info.version, app_dir)  # create installer (may be None in CI)

            if self.upload and installer_exe_path is not None:
                if self.cloud_profile is None and self.cloud_id is None:
                    pyship_print("no cloud access provided - will not attempt upload")
                else:
                    # if cloud bucket not given we'll try to use the project name
                    assert isinstance(target_app_info.name, str)
                    assert isinstance(target_app_info.author, str)
                    bucket = create_bucket_name(target_app_info.name, target_app_info.author) if self.cloud_bucket is None else self.cloud_bucket

                    # use either a cloud profile (i.e. credentials usually stored in local file(s) ) or explicit cloud credentials
                    if self.cloud_profile is None:
                        if self.cloud_secret is None:
                            log.error(f"{self.cloud_secret=}")
                            s3_access = None
                        else:
                            s3_access = S3Access(bucket, aws_access_key_id=self.cloud_id, aws_secret_access_key=self.cloud_secret)
                    else:
                        s3_access = S3Access(bucket, profile_name=self.cloud_profile)

                    if s3_access is not None:
                        s3_access.public_readable = self.public_readable
                        self.cloud_access = PyShipCloud(target_app_info.name, s3_access)

                        installer_url = self.cloud_access.upload(installer_exe_path)  # upload installer file
                        pyship_print(f'uploaded "{installer_exe_path}" to {installer_url}')

                        clip_url = self.cloud_access.upload(clip_file_path)  # upload clip file
                        pyship_print(f'uploaded "{clip_file_path}" to {clip_url}')

            else:
                pyship_print("no upload requested")

            elapsed_time = datetime.now() - start_time
            pyship_print(f"{pyship_application_name} done (elapsed_time={str(elapsed_time)})")

        return installer_exe_path
