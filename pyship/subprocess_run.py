import subprocess
from pathlib import Path

from typeguard import typechecked

from pyship import __application_name__, ok_return_code, restart_return_code, error_return_code, pyship_print, get_logger

log = get_logger(__application_name__)


@typechecked(always=True)
def subprocess_run(cmd: list, cwd: Path = None, is_gui: bool = False) -> int:

    if cwd is not None:
        cwd = str(cwd)  # subprocess requires a string

    try:
        log.info(cmd)
        target_process = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if target_process.returncode != ok_return_code and target_process.returncode != restart_return_code:
            for out in [target_process.stdout, target_process.stderr]:
                if out is not None and len(out.strip()) > 0:
                    log.warning(out)

        # if not is_gui:
        #     for out in [target_process.stdout, target_process.stderr]:
        #         if out is not None and len(out.strip()) > 0:
        #             print(out)

        return_code = target_process.returncode

    except FileNotFoundError as e:
        log.error(f"{e} {cmd}")
        return_code = error_return_code

    return return_code
