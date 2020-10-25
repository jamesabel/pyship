import sys
from pathlib import Path
import subprocess

from typeguard import typechecked

from pyshipupdate import mkdirs
import pyship
from pyship import AppInfo, pyship_print, get_logger, get_icon
from pyship import __application_name__ as pyship_application_name
from pyship.launcher import application_name as launcher_application_name
from pyship.launcher import calculate_launcher_metadata, load_launcher_metadata, store_launcher_metadata


log = get_logger(launcher_application_name)


@typechecked(always=True)
def create_launcher(target_app_info: AppInfo, app_path_output: Path):
    """
    create the launcher executable
    :param target_app_info: target app info
    :param app_path_output: app gets built here
    :return: True if launcher was built
    """

    built_it = False

    if target_app_info.name is None or len(target_app_info.name) < 1:
        log.error(f"{target_app_info.name=}")
    else:

        launcher_metadata_filename = f"{target_app_info.name}_metadata.json"

        # create launcher

        # find the launcher source file path
        pyship_path_list = pyship.__path__
        if len(pyship_path_list) != 1:
            log.warning(f"not length of 1: {pyship_path_list}")
        pyship_path = pyship_path_list[0]  # parent dir of launcher source
        launcher_module_dir = Path(pyship_path, launcher_application_name)

        launcher_exe_filename = f"{target_app_info.name}.exe"
        launcher_exe_path = Path(app_path_output, target_app_info.name, launcher_exe_filename)

        icon_path = get_icon(target_app_info, pyship_print)

        python_interpreter_path = sys.executable
        if python_interpreter_path is None or len(python_interpreter_path) < 1:
            log.error(f"python interpreter path not found")
        else:

            mkdirs(app_path_output)

            explicit_modules_to_import = ["ismain", "sentry_sdk", "typeguard", "sentry_sdk.integrations.stdlib", "pywin32",
                                          "pyshipupdate", # todo: remove this once pyship's wheel requires pyshipupdate
                                          "pyship"  # pyship is needed since launcher calls other routines in pyship
                                          ]

            venv_dir = Path(target_app_info.project_dir, "venv")  # venv for the target app
            pyinstaller_exe_path = Path(venv_dir, "Scripts", "pyinstaller.exe")
            if not pyinstaller_exe_path.exists():
                raise FileNotFoundError(str(pyinstaller_exe_path))
            command_line = [str(pyinstaller_exe_path), "--clean", "-i", str(icon_path), "-n", target_app_info.name, "--distpath", str(app_path_output.absolute())]
            for explicit_module_to_import in explicit_modules_to_import:
                # modules pyinstaller doesn't seem to be able to find on its own
                command_line.extend(["--hiddenimport", explicit_module_to_import])

            # "-F" or "--onefile" is too slow of a start up - was measured at 15 sec for the launch app (experiment with just a print as the app was still 2 sec startup).  --onedir is ~1 sec.
            # I could probably get the full app down a bit, but it'll never be 1 sec.
            # https://stackoverflow.com/questions/9469932/app-created-with-pyinstaller-has-a-slow-startup
            # command_line.append("--onefile")
            command_line.append("--onedir")

            if target_app_info.is_gui:
                command_line.append("--noconsole")
            # command_line.extend(["--debug", "all"])  # todo: remove once we get the launcher working again
            site_packages_dir = Path(venv_dir, "Lib", "site-packages")
            launcher_path = Path(site_packages_dir, pyship_application_name, launcher_application_name, f"{launcher_application_name}.py").absolute()
            if not launcher_path.exists():
                log.error("{launcher_path} does not exist")
            command_line.append(str(launcher_path))

            # avoid re-building launcher if its functionality wouldn't change
            launcher_metadata = calculate_launcher_metadata(target_app_info.name, target_app_info.author, Path(launcher_module_dir), icon_path, target_app_info.is_gui)
            if not launcher_exe_path.exists() or launcher_metadata != load_launcher_metadata(app_path_output, launcher_metadata_filename):

                pyship_print(f"building launcher ({launcher_exe_path})")
                log.info(f"project_dir={str(target_app_info.project_dir)}")
                log.info(f"{command_line=}")
                # pyinstaller outputs regular status messages to stderr for some reason so just capture all output but also check for error return code
                launcher_run = subprocess.run(command_line, cwd=target_app_info.project_dir, capture_output=True, text=True, check=True)
                # metadata is in the app parent dir
                store_launcher_metadata(app_path_output, launcher_metadata_filename, launcher_metadata)

                if launcher_exe_path.exists():
                    built_it = True
                    pyship_print(f"launcher built ({launcher_exe_path})")
                else:
                    # launcher wasn't built - there was an error - so display the pyinstaller output to the user
                    pyship_print(launcher_run.std_out)
                    pyship_print(launcher_run.std_err)
            else:
                pyship_print(f"{launcher_exe_path} already built - no need to rebuild")

    return built_it
