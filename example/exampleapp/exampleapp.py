import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

from . import __application_name__, __version__


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{__application_name__} {__version__}")
        self.setFixedSize(400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        title_label = QLabel(f"Hello from pyship!")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title_label)

        version_label = QLabel(f"{__application_name__} v{__version__}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("font-size: 14px; color: gray;")
        layout.addWidget(version_label)

        self.click_count = 0
        self.button = QPushButton("Click Me")
        self.button.setStyleSheet("font-size: 16px; padding: 10px;")
        self.button.clicked.connect(self.on_click)
        layout.addWidget(self.button)

        self.count_label = QLabel("Clicks: 0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.count_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.count_label)


    def on_click(self):
        self.click_count += 1
        self.count_label.setText(f"Clicks: {self.click_count}")


def exampleapp():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
