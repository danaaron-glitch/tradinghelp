# settings.py

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import pyqtSignal, Qt
from datetime import datetime


class SettingsWidget(QWidget):
    fullscreen_requested = pyqtSignal(bool)
    color_theme_changed = pyqtSignal(str)  # Signal to emit the selected theme stylesheet

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Fetch and Save Stock Data Button
        self.fetch_data_button = QPushButton('Fetch and Save Stock Data', self)
        layout.addWidget(self.fetch_data_button)

        # Timestamp Label
        self.timestamp_label = QLabel(self)
        self.update_timestamp(datetime.now())  # Initialize with the current time (for demonstration)
        layout.addWidget(self.timestamp_label)

        # Theme Selection Dropdown
        self.theme_dropdown = QComboBox(self)
        self.theme_dropdown.addItem("Dark Theme")
        self.theme_dropdown.addItem("Light Theme")
        self.theme_dropdown.addItem("Custom Theme")
        self.theme_dropdown.addItem("Pikachu Theme")
        self.theme_dropdown.addItem("Gay Theme")
        self.theme_dropdown.currentIndexChanged.connect(self.switch_theme)
        layout.addWidget(self.theme_dropdown)

        # Exit Program Button
        self.exit_button = QPushButton('Exit Program', self)
        layout.addWidget(self.exit_button)

        self.setLayout(layout)

        # Store the available themes
        self.themes = [
            self.dark_theme(),
            self.light_theme(),
            self.custom_theme(),
            self.pikachu_theme(),
            self.gay_theme()
        ]

    def update_timestamp(self, timestamp):
        formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        self.timestamp_label.setText(f"Last Data Fetch: {formatted_time}")

    def switch_theme(self):
        # Get the selected theme index
        selected_index = self.theme_dropdown.currentIndex()
        # Emit corresponding theme stylesheet
        self.color_theme_changed.emit(self.themes[selected_index])

    @staticmethod
    def dark_theme():
        return """
        QWidget {
            background-color: #2e2e2e;
            color: #ffffff;
        }
        QPushButton, QComboBox, QLineEdit, QLabel {
            background-color: #2e2e2e;
            color: #ffffff;
            border: none;
        }
        """

    @staticmethod
    def light_theme():
        return """
        QWidget {
            background-color: #ffffff;
            color: #000000;
        }
        QPushButton, QComboBox, QLineEdit, QLabel {
            background-color: #ffffff;
            color: #000000;
            border: none;
        }
        """

    @staticmethod
    def custom_theme():
        return """
        QWidget {
            background-color: #121212;
            color: #ff5722;
        }
        QPushButton, QComboBox, QLineEdit, QLabel {
            background-color: #121212;
            color: #ff5722;
            border: none;
        }
        """

    @staticmethod
    def pikachu_theme():
        return """
        QWidget {
            background-color: #ffeb3b;
            color: #c2185b;
        }
        QPushButton, QComboBox, QLineEdit, QLabel {
            background-color: #ffeb3b;
            color: #c2185b;
            border: none;
        }
        """

    @staticmethod
    def gay_theme():
        return """
        QWidget {
            background-color: #ffffff;
            color: #000000;
        }
        QPushButton {
            background: linear-gradient(to right, #ff0000, #ff9900, #ffee00, #119933, #1325b5, #cc338b);
            color: #ffffff;
            border: none;
        }
        QPushButton:hover {
            background: linear-gradient(to right, #cc338b, #1325b5, #119933, #ffee00, #ff9900, #ff0000);
        }
        QComboBox, QLineEdit, QLabel {
            background-color: #ffffff;
            color: #000000;
            border: none;
        }
        """
