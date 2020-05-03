import os
import subprocess
import sys
import shutil
from pathlib import Path

from typeguard import typechecked

import pyship
from pyship import TargetAppInfo, pyship_print, log_process_output, get_logger
from pyship.launcher import application_name as launcher_application_name, calculate_launcher_metadata, load_launcher_metadata, store_launcher_metadata


log = get_logger(launcher_application_name)


@typechecked(always=True)
def create_launcher(target_app_info: TargetAppInfo, dist_path: Path):
    """
    create the launcher executable
    :param target_app_info: target app info
    :param dist_path: dist path
    :return: True if launcher was built
    """

    built_it = False

    launcher_metadata_filename = f"{target_app_info.name}_metadata.json"

    # create launcher

    # find the launcher source file path
    pyship_path_list = pyship.__path__
    if len(pyship_path_list) != 1:
        log.warning(f"not length of 1: {pyship_path_list}")
    pyship_path = pyship_path_list[0]  # parent dir of launcher source
    launcher_module_dir = Path(pyship_path, launcher_application_name)
    launcher_source_file_name = f"launcher.py"
    launcher_source_path = os.path.join(launcher_module_dir, launcher_source_file_name)

    launcher_exe_filename = f"{target_app_info.name}.exe"
    launcher_exe_path = Path(dist_path, launcher_exe_filename)
    icon_path = Path(target_app_info.name, f"{target_app_info.name}.ico").absolute()

    python_interpreter_path = sys.executable
    if python_interpreter_path is None or len(python_interpreter_path) < 1:
        log.error(f"python interpreter path not found")
    else:

        dist_path.mkdir(parents=True, exist_ok=True)

        pyinstaller_exe_path = Path(Path(sys.executable).parent, "pyinstaller.exe")  # pyinstaller executable is in the same directory as the python interpreter
        if not pyinstaller_exe_path.exists():
            raise FileNotFoundError(str(pyinstaller_exe_path))
        command_line = [str(pyinstaller_exe_path), "--clean", "-i", str(icon_path), "-n", target_app_info.name, "--distpath", str(dist_path.absolute())]

        # "-F" or "--onefile" is too slow of a start up - was measured at 15 sec for the launch app (experiment with just a print as the app was still 2 sec startup).  --onedir is ~1 sec.
        # I could probably get the full app down a bit, but it'll never be 1 sec.
        # https://stackoverflow.com/questions/9469932/app-created-with-pyinstaller-has-a-slow-startup
        # command_line.append("--onefile")
        command_line.append("--onedir")

        if target_app_info.is_gui:
            command_line.append("--noconsole")
        command_line.append(launcher_source_file_name)

        # avoid re-building launcher if its functionality wouldn't change
        launcher_metadata = calculate_launcher_metadata(target_app_info.name, Path(launcher_source_path), icon_path, target_app_info.is_gui)
        if not launcher_exe_path.exists() or launcher_metadata != load_launcher_metadata(dist_path, launcher_metadata_filename):
            try:
                os.unlink(launcher_exe_path)
            except FileNotFoundError:
                pass
            pyship_print(f"building launcher ({launcher_exe_path})", )
            pyship_print(f"{command_line}")
            launcher_run = subprocess.run(command_line, cwd=launcher_module_dir, capture_output=True)
            store_launcher_metadata(dist_path, launcher_metadata_filename, launcher_metadata)

            # log/print pyinstaller output
            log_lines = {}
            for output_type, output_bytes in [("stdout", launcher_run.stdout), ("stderr", launcher_run.stderr)]:
                log_lines[output_type] = log_process_output(output_type, output_bytes)

            if launcher_exe_path.exists():
                built_it = True
                pyship_print(f"launcher build ({launcher_exe_path})")
            else:
                # launcher wasn't built - there was an error - so display the pyinstaller output to the user
                for output_type, log_lines in log_lines.items():
                    pyship_print(f"{output_type}:")
                    for log_line in log_lines:
                        pyship_print(log_line)
        else:
            pyship_print(f"{launcher_exe_path} already built - no need to rebuild")

    return built_it
