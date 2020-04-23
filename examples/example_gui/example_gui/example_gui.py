import sys

from PyQt5.QtWidgets import QMessageBox, QApplication
from ismain import is_main

__title__ = "example_gui"


def example_gui():
    app = QApplication(sys.argv)
    mb = QMessageBox()
    mb.setIcon(QMessageBox.Information)
    mb.setWindowTitle(__title__)
    mb.setText(f"Congratulations - you have successfully run the {__title__} example!")
    mb.setStandardButtons(QMessageBox.Ok)
    mb.show()
    app.exec_()


if is_main():
    example_gui()
