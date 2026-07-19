"""
User-facing output: :func:`pyship_print` combines logging with a timestamped
console print (or a tkinter label in GUI mode).
"""

from tkinter import Tk, Label
from datetime import datetime

from typeguard import typechecked
from balsa import get_logger

from pyship import __application_name__

log = get_logger(__application_name__)

window = Tk()
window.withdraw()  # no main window


@typechecked
def pyship_print(s: str, ui: str = "cli"):
    """
    Emit a user-facing message: always logged, and shown on the console
    (timestamped) or in a GUI window depending on *ui*.

    :param s: message to display
    :param ui: "cli" (default) for console output, "gui" for a tkinter window
    """
    log.info(s)
    if ui == "gui":
        label = Label(window, text=s)  # adds to the window each time
        label.grid()
        label.update()
        window.deiconify()
    else:
        print_string = f"{datetime.now().astimezone().isoformat()} : {s}"
        print(print_string)
