"""
User-facing output: :func:`pyship_print` combines logging with a timestamped
console print (or a tkinter label in GUI mode).

tkinter is imported lazily, and only for GUI mode - importing this module (and
therefore the pyship package) must work in headless environments without a
display or a tkinter installation.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Union

from typeguard import typechecked
from balsa import get_logger

from pyship import __application_name__

if TYPE_CHECKING:
    from tkinter import Tk

log = get_logger(__application_name__)

# hidden tkinter root window for GUI-mode output, created on first use
_window: Union["Tk", None] = None


def _get_window() -> Union["Tk", None]:
    """
    Create (once) and return the hidden tkinter root window used for GUI-mode
    output, or None if tkinter is unavailable (headless environment).
    """
    global _window
    if _window is None:
        try:
            from tkinter import Tk

            _window = Tk()
            _window.withdraw()  # no main window until there is something to show
        except Exception as exc:
            log.warning(f"tkinter unavailable, falling back to console output: {exc}")
    return _window


@typechecked
def pyship_print(s: str, ui: str = "cli"):
    """
    Emit a user-facing message: always logged, and shown on the console
    (timestamped) or in a GUI window depending on *ui*.

    In GUI mode, falls back to console output if tkinter is unavailable.

    :param s: message to display
    :param ui: "cli" (default) for console output, "gui" for a tkinter window
    """
    log.info(s)
    if ui == "gui":
        window = _get_window()
        if window is not None:
            from tkinter import Label

            label = Label(window, text=s)  # adds to the window each time
            label.grid()
            label.update()
            window.deiconify()
            return
    print(f"{datetime.now().astimezone().isoformat()} : {s}")
