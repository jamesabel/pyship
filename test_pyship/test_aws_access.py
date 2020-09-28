# import time
# from pathlib import Path
#
# from ismain import is_main
#
# from pyship import PyshipLog, get_logger, __author__
# from pyship.aws import AWSS3Bucket
#
# test_bucket_name = "pyshiptest"
#
# log = get_logger(__name__)
#
#
# def test_aws_access():
#     aws_s3_bucket = AWSS3Bucket(bucket_name=test_bucket_name)
#     assert aws_s3_bucket.bucket_exists()
#
#
# def test_aws_upload_download():
#     test_string = str(time.time())
#     test_file_name = "test.txt"
#     temp_dir = "temp"
#     temp_file_path = Path(temp_dir, test_file_name)
#
#     # upload
#     with temp_file_path.open("w") as f:
#         f.write(test_string)
#     aws_s3_bucket = AWSS3Bucket(bucket_name=test_bucket_name)
#     aws_s3_bucket.upload(temp_file_path, force=True)
#
#     # download
#     temp_file_path_download = Path(temp_dir, "test2.txt")
#     aws_s3_bucket.download(temp_file_path_download, test_file_name)
#     with temp_file_path_download.open() as f:
#         download_string = f.read().strip()
#     assert download_string == test_string
#
#     # bucket dir
#     bucket_dir = aws_s3_bucket.dir()
#     assert bucket_dir[test_file_name].size == len(test_string)
#
#
# if is_main():
#     pyship_log = PyshipLog(__name__, __author__, verbose=True)
#     pyship_log.init_logger()
#     test_aws_access()
#     test_aws_upload_download()
