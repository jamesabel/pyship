from pathlib import Path
from datetime import datetime

import appdirs
from attr import attrs
from typeguard import typechecked
from awsimple import S3Access

from pyshipupdate import mkdirs, create_bucket_name
from pyshipupdate import __version__ as pyshipupdate_version
from pyship import __application_name__ as pyship_application_name
from pyship import __author__ as pyship_author
from pyship import __version__ as pyship_version
from pyship import AppInfo, get_logger, run_nsis, create_clip, create_launcher, pyship_print, APP_DIR_NAME, create_clip_file, DEFAULT_DIST_DIR_NAME, get_app_info, PyShipCloud

log = get_logger(pyship_application_name)


@attrs(auto_attribs=True)
class PyShip:

    project_dir: Path = Path()  # target app project dir, e.g. the "home" directory of the project.  If None, current working directory is used.
    dist_dir: Path = Path(DEFAULT_DIST_DIR_NAME)  # many packaging tools (e.g filt, etc.) use "dist" as the package destination directory
    find_links: list = []  # extra dirs for pip to use for packages not yet on PyPI (e.g. under local development)
    cache_dir: Path = Path(appdirs.user_cache_dir(pyship_application_name, pyship_author))  # used to cache things like the embedded Python zip (to keep us off the python.org servers)

    # cloud credentials, locations, etc.
    cloud_bucket = None  # e.g. AWS S3 bucket
    cloud_profile: str = None  # e.g. AWS IAM profile
    cloud_id: str = None  # e.g. AWS Access Key ID
    cloud_secret: str = None  # e.g. AWS Secret Access Key
    cloud_access: PyShipCloud = None  # making this accessible outside this class aids in testing, especially when mocking

    @typechecked(always=True)
    def ship(self) -> (Path, None):
        """
        Perform all the steps to ship the app, including creating the installer.
        :return: the path to the created installer or None if it could not be created
        """

        start_time = datetime.now()
        pyship_print(f"{pyship_application_name} starting (pyship={str(pyship_version)},pyshipupdate={str(pyshipupdate_version)})")

        target_app_info = get_app_info(self.project_dir, self.dist_dir)

        installer_exe_path = None
        if self.project_dir is None:
            log.error(f"{self.project_dir=}")
        elif target_app_info is None:
            log.error(f"{target_app_info=}")
        elif target_app_info.name is None:
            log.error(f"{target_app_info.name=}")
        else:

            if self.cloud_profile is None and self.cloud_id is None:
                pyship_print("no cloud access provided - will not attempt upload")

            app_dir = Path(self.project_dir, APP_DIR_NAME, target_app_info.name).absolute()

            mkdirs(app_dir, remove_first=True)

            create_launcher(target_app_info, app_dir)  # create the OS specific launcher executable

            clip_dir = create_clip(target_app_info, app_dir, True, Path(self.project_dir, self.dist_dir), self.cache_dir, self.find_links)

            clip_file_path = create_clip_file(clip_dir)  # create clip file
            installer_exe_path = run_nsis(target_app_info, target_app_info.version, app_dir)  # create installer

            if self.cloud_profile is not None or self.cloud_id is not None:

                # if cloud bucket not given we'll try to use the project name
                bucket = create_bucket_name(target_app_info.name, target_app_info.author) if self.cloud_bucket is None else self.cloud_bucket

                # use either a cloud profile (i.e. credentials usually stored in local file(s) ) or explicit cloud credentials
                if self.cloud_profile is not None:
                    s3_access = S3Access(bucket, profile_name=self.cloud_profile)
                else:
                    s3_access = S3Access(bucket, aws_access_key_id=self.cloud_id, aws_secret_access_key=self.cloud_secret)
                self.cloud_access = PyShipCloud(target_app_info.name, s3_access)

                pyship_print(f"uploading {installer_exe_path} to {self.cloud_access. s3_access.bucket_name}/{installer_exe_path.name}")
                self.cloud_access.upload(installer_exe_path)  # upload installer file

                pyship_print(f"uploading {clip_file_path} to {s3_access.bucket_name}/{clip_file_path.name}")
                self.cloud_access.upload(clip_file_path)  # upload clip file

            elapsed_time = datetime.now() - start_time
            pyship_print(f"{pyship_application_name} done (elapsed_time={str(elapsed_time)})")

        return installer_exe_path
