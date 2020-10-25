from tkinter import Tk, Label
from datetime import datetime

from typeguard import typechecked

from pyship import get_logger, __application_name__

log = get_logger(__application_name__)

window = Tk()
window.withdraw()  # no main window


@typechecked(always=True)
def pyship_print(s: str, is_gui: bool = False):
    log.info(s)
    if is_gui:
        global window
        label = Label(window, text=s)  # adds to the window each time
        label.grid()
        label.update()
        window.deiconify()
    else:
        print_string = f"{datetime.now().astimezone().isoformat()} : {s}"
        print(print_string)
