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
    log.info(s)
    if ui == "gui":
        label = Label(window, text=s)  # adds to the window each time
        label.grid()
        label.update()
        window.deiconify()
    else:
        print_string = f"{datetime.now().astimezone().isoformat()} : {s}"
        print(print_string)
