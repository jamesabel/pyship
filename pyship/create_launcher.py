import shutil
from pathlib import Path

from typeguard import typechecked
from balsa import get_logger
from semver import VersionInfo

from pyshipupdate import mkdirs
import pyship
from pyship import AppInfo, pyship_print, get_icon
from pyship import __application_name__ as pyship_application_name
from pyship.launcher import application_name as launcher_application_name
from pyship.launcher import calculate_metadata, load_metadata, store_metadata
from pyship.launcher_stub import compile_launcher_stub


log = get_logger(launcher_application_name)


@typechecked
def create_pyship_launcher(target_app_info: AppInfo, app_path_output: Path):
    """
    Create the launcher executable using a compiled C# stub and standalone Python launcher script.
    :param target_app_info: target app info
    :param app_path_output: app gets built here
    :return: True if launcher was built
    """

    built_it = False

    if target_app_info.name is None or len(target_app_info.name) < 1:
        log.error(f"{target_app_info.name=}")
    else:
        metadata_filename = f"{target_app_info.name}_metadata.json"

        # find the launcher source directory (for metadata hashing)
        assert hasattr(pyship, "__path__")
        pyship_path_list = pyship.__path__  # type: ignore
        if len(pyship_path_list) != 1:
            log.warning(f"not length of 1: {pyship_path_list}")
        pyship_path = Path(pyship_path_list[0])
        launcher_module_dir = Path(pyship_path, launcher_application_name)

        launcher_dir = Path(app_path_output, target_app_info.name)
        launcher_exe_path = Path(launcher_dir, f"{target_app_info.name}.exe")

        icon_path = get_icon(target_app_info, pyship_print)

        mkdirs(app_path_output)

        # Compute metadata for cache invalidation
        assert isinstance(target_app_info.author, str)
        assert isinstance(target_app_info.is_gui, bool)
        assert isinstance(target_app_info.version, VersionInfo)
        metadata = calculate_metadata(target_app_info.name, target_app_info.author, target_app_info.version, launcher_module_dir, icon_path, target_app_info.is_gui)
        if not launcher_exe_path.exists() or metadata != load_metadata(app_path_output, metadata_filename):
            pyship_print(f'building launcher ("{launcher_exe_path}")')

            # 1. Compile the C# stub
            compile_launcher_stub(
                app_name=target_app_info.name,
                icon_path=icon_path,
                is_gui=target_app_info.is_gui,
                output_path=launcher_dir,
            )

            # 2. Copy the standalone launcher script alongside the stub
            standalone_source = Path(launcher_module_dir, "launcher_standalone.py")
            standalone_dest = Path(launcher_dir, f"{target_app_info.name}_launcher.py")
            shutil.copy2(str(standalone_source), str(standalone_dest))
            log.info(f"copied launcher script to {standalone_dest}")

            # 3. Copy the icon alongside
            if icon_path.exists():
                icon_dest = Path(launcher_dir, f"{target_app_info.name}.ico")
                shutil.copy2(str(icon_path), str(icon_dest))
                log.info(f"copied icon to {icon_dest}")

            # 4. Store metadata for cache invalidation
            store_metadata(app_path_output, metadata_filename, metadata)

            if launcher_exe_path.exists():
                built_it = True
                log.info(f"launcher built ({launcher_exe_path})")
            else:
                log.error(f"launcher exe not found after build: {launcher_exe_path}")
        else:
            log.info(f"{launcher_exe_path} already built - no need to rebuild")

    return built_it
