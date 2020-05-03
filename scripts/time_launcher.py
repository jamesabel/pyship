from pathlib import Path
import time
import subprocess
import shutil

from pyship import create_launcher, TargetAppInfo, __application_name__

from ismain import is_main

if is_main():
    target_app_info = TargetAppInfo()  # picks up pyship info from pyship's pyproject.toml
    dist_dir = Path("temp", "dist")
    shutil.rmtree(dist_dir)
    create_launcher(target_app_info, dist_dir)
    exe_path = Path(dist_dir, __application_name__, f"{__application_name__}.exe")
    print(exe_path)
    for iteration in range(0, 6):
        start = time.time()
        launcher_process = subprocess.run(exe_path, cwd=dist_dir, capture_output=True)  # the launcher won't actually work, but we're just trying to time it
        end = time.time()
        print(f"{end - start} sec")
        if iteration == 0:
            print(launcher_process.stdout.decode())
            print(launcher_process.stderr.decode())
