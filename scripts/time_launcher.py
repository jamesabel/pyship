from pathlib import Path
import time
import subprocess
import shutil

from pyship import create_launcher, __application_name__, AppInfo

from ismain import is_main

if is_main():

    # benchmark how long it takes for the launcher to start up

    exe_path = Path("app", __application_name__, f"{__application_name__}.exe").resolve().absolute()
    print(exe_path)
    for iteration in range(0, 6):
        start = time.time()
        launcher_process = subprocess.run(exe_path, cwd=exe_path.parent, capture_output=True)  # the launcher won't actually work, but we're just trying to time it
        end = time.time()
        print(f"{end - start} sec")
        if iteration == 0:
            print(launcher_process.stdout.decode())
            print(launcher_process.stderr.decode())
