import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QMessageBox,
    QStackedWidget, QLabel, QHBoxLayout, QFrame, QSizePolicy, QDialog,
    QComboBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWebEngineWidgets import QWebEngineView
import plotly.io as pio
from datetime import datetime

from stockcomparison import StockComparisonWidget
from sectorcomparison import SectorComparisonWidget
from focus import FocusView
from sentanalysis import SentimentAnalysis
from dashboard import DashboardWidget  # Import DashboardWidget

# Ensure you have these styles available
dark_theme = """
QWidget {
    background-color: #2E2E2E;
    color: white;
}
QPushButton {
    background-color: #595959;
    color: white;
}
QFrame#sidebarFrame {
    background-color: #1E1E1E;
}
QPushButton#sidebarButton {
    background-color: #1E1E1E;
    text-align: left;
    padding-left: 10px;
    border: none;
}
QPushButton#sidebarButton:hover {
    background-color: #353535;
}
"""

light_theme = """
QWidget {
    background-color: #FFFFFF;
    color: black;
}
QPushButton {
    background-color: #E0E0E0;
    color: black;
}
QFrame#sidebarFrame {
    background-color: #F0F0F0;
}
QPushButton#sidebarButton {
    background-color: #F0F0F0;
    text-align: left;
    padding-left: 10px;
    border: none;
}
QPushButton#sidebarButton:hover {
    background-color: #D0D0D0;
}
"""


# Combobox style
def apply_combobox_style(combobox):
    combobox.setStyleSheet("""
    QComboBox {
        padding: 5px;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
    }
    """)


# Define your SettingsDialog
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.parent = parent
        self.setWindowTitle("Settings")
        self.setGeometry(150, 150, 400, 300)

        layout = QVBoxLayout()

        self.theme_combobox = QComboBox(self)
        self.theme_combobox.addItems(["Dark Theme", "Light Theme"])
        self.theme_combobox.currentIndexChanged.connect(self.change_color_theme)
        layout.addWidget(QLabel("Select Color Theme"))
        layout.addWidget(self.theme_combobox)

        self.fullscreen_button = QPushButton("Toggle Fullscreen", self)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        layout.addWidget(self.fullscreen_button)

        self.fetch_data_button = QPushButton("Fetch Stock Data", self)
        self.fetch_data_button.clicked.connect(parent.on_click)
        layout.addWidget(self.fetch_data_button)

        self.exit_button = QPushButton("Exit", self)
        self.exit_button.clicked.connect(self.close_program)
        layout.addWidget(self.exit_button)

        self.setLayout(layout)
        apply_combobox_style(self.theme_combobox)

    def change_color_theme(self):
        theme = self.theme_combobox.currentText()
        if theme == "Dark Theme":
            self.parent.apply_new_theme(dark_theme)
        elif theme == "Light Theme":
            self.parent.apply_new_theme(light_theme)

    def toggle_fullscreen(self):
        self.parent.toggle_fullscreen(not self.parent.isFullScreen())

    def close_program(self):
        QApplication.quit()

    def update_timestamp(self, timestamp):
        self.fetch_data_button.setText(f"Last fetched: {timestamp:%Y-%m-%d %H:%M:%S}")


# Define the StockDataWorker
class StockDataWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def run(self):
        try:
            # Dummy path for demonstration. Replace with actual path logic to fetch or download the file.
            data_directory = 'stock_data'
            self.finished.emit(data_directory)
        except Exception as e:
            self.error.emit(f"Unexpected error: {str(e)}")


# Define SentimentAnalysisWidget
class SentimentAnalysisWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.analysis = SentimentAnalysis()

        self.layout = QVBoxLayout()
        self.label = QLabel('Sentiment Analysis View', self)
        self.layout.addWidget(self.label)

        self.fetch_button = QPushButton('Fetch Sentiment Scores', self)
        self.fetch_button.clicked.connect(self.fetch_sentiment_scores)
        self.layout.addWidget(self.fetch_button)

        self.graph_view = QWebEngineView(self)
        self.layout.addWidget(self.graph_view)

        self.setLayout(self.layout)

    def fetch_sentiment_scores(self):
        fig = self.analysis.get_plotly_figure()
        html_content = pio.to_html(fig, full_html=False)
        self.graph_view.setHtml(html_content)


# Define the App class
class App(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'Stock Data Fetcher'
        self.initUI()
        self.worker = StockDataWorker()
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 800, 600)
        layout = QHBoxLayout()

        self.sidebar = QVBoxLayout()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setContentsMargins(0, 0, 0, 0)
        self.sidebar.setSpacing(0)
        self.sidebar.setAlignment(Qt.AlignTop)

        self.buttons = {}

        # Create instances of the widgets
        self.dashboard = DashboardWidget(self)
        self.focus_view = FocusView(self)
        self.stock_comparison = StockComparisonWidget(self)
        self.sector_comparison = SectorComparisonWidget(self)
        self.strategy_tester = QWidget()
        self.strategy_tester_layout = QVBoxLayout()
        self.strategy_tester_label = QLabel('Strategy Tester View')
        self.strategy_tester_layout.addWidget(self.strategy_tester_label)
        self.strategy_tester.setLayout(self.strategy_tester_layout)

        self.opportunity_finder = QWidget()
        self.opportunity_finder_layout = QVBoxLayout()
        self.opportunity_finder_label = QLabel('Opportunity Finder View')
        self.opportunity_finder_layout.addWidget(self.opportunity_finder_label)
        self.opportunity_finder.setLayout(self.opportunity_finder_layout)

        self.sentiment_analysis = SentimentAnalysisWidget(self)

        self.settings = QWidget()
        self.settings_layout = QVBoxLayout()
        self.settings_label = QLabel('Settings View')
        self.settings_layout.addWidget(self.settings_label)
        self.settings.setLayout(self.settings_layout)

        # Add sidebar buttons
        self.add_sidebar_button("Dashboard", self.display_dashboard, self.dashboard)
        self.add_sidebar_button("Focus View", self.display_focus_view, self.focus_view)
        self.add_sidebar_button("Stock Comparison", self.display_stock_comparison, self.stock_comparison)
        self.add_sidebar_button("Sector Comparison", self.display_sector_comparison, self.sector_comparison)
        self.add_sidebar_button("Strategy Tester", self.display_strategy_tester, self.strategy_tester)
        self.add_sidebar_button("Opportunity Finder", self.display_opportunity_finder, self.opportunity_finder)
        self.add_sidebar_button("Sentiment Analysis", self.display_sentiment_analysis, self.sentiment_analysis)
        self.add_sidebar_button("Settings", self.on_settings_click, self.settings)

        sidebar_frame = QFrame(self)
        sidebar_frame.setLayout(self.sidebar)
        sidebar_frame.setFixedWidth(250)
        sidebar_frame.setObjectName("sidebarFrame")

        layout.addWidget(sidebar_frame)

        self.stack = QStackedWidget(self)
        layout.addWidget(self.stack)

        # Add widgets to the stack
        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.focus_view)
        self.stack.addWidget(self.stock_comparison)
        self.stack.addWidget(self.sector_comparison)
        self.stack.addWidget(self.strategy_tester)
        self.stack.addWidget(self.opportunity_finder)
        self.stack.addWidget(self.sentiment_analysis)
        self.stack.addWidget(self.settings)

        self.setLayout(layout)
        self.apply_styles()
        self.display_dashboard()  # Initial view

    def add_sidebar_button(self, text, callback, widget):
        button = QPushButton(text, self)
        button.setObjectName("sidebarButton")
        button.setFont(QFont("Arial", 10))
        button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        button.setFixedHeight(30)
        button.clicked.connect(lambda: self.on_sidebar_button_click(callback, button))
        self.sidebar.addWidget(button)
        self.buttons[button] = widget

    def on_sidebar_button_click(self, callback, button):
        for btn in self.buttons:
            btn.setStyleSheet('')
        button.setStyleSheet("""
            background-color: #2a82da;
            color: white;
        """)
        callback()

    def display_dashboard(self):
        self.stack.setCurrentWidget(self.dashboard)

    def display_focus_view(self):
        self.stack.setCurrentWidget(self.focus_view)

    def display_stock_comparison(self):
        self.stack.setCurrentWidget(self.stock_comparison)
        self.stock_comparison.on_compare_button_click()

    def display_sector_comparison(self):
        self.stack.setCurrentWidget(self.sector_comparison)

    def display_strategy_tester(self):
        self.stack.setCurrentWidget(self.strategy_tester)

    def display_opportunity_finder(self):
        self.stack.setCurrentWidget(self.opportunity_finder)

    def display_sentiment_analysis(self):
        self.stack.setCurrentWidget(self.sentiment_analysis)

    def on_settings_click(self):
        self.settings_dialog = SettingsDialog(self)
        self.settings_dialog.exec_()

    def on_click(self):
        self.progress = QMessageBox.information(self, "Please Wait", "Fetching stock data...")
        self.worker.start()

    def on_finished(self, data_directory):
        self.progress.hide()
        if hasattr(self, 'settings_dialog'):
            self.settings_dialog.update_timestamp(datetime.now())
        self.focus_view.load_stock_data(data_directory)
        QMessageBox.information(self, "Success", "Stock data successfully fetched and saved!")

    def on_error(self, error_message):
        self.progress.hide()
        QMessageBox.critical(self, "Error", f"An error occurred: {error_message}")

    def toggle_fullscreen(self, fullscreen):
        if fullscreen:
            self.showFullScreen()
        else:
            self.showMaximized()

    def apply_new_theme(self, stylesheet):
        self.setStyleSheet(stylesheet)

    def apply_styles(self):
        self.setStyleSheet(dark_theme)


# Main function to run the app
def main():
    try:
        # Initialize the application
        app = QApplication(sys.argv)
        # Create an instance of your main application window
        ex = App()
        # Show the main window maximized
        ex.showMaximized()
        # Execute the application's event loop
        sys.exit(app.exec_())
    except Exception as e:
        # In case of an exception, print the error to standard error
        print(f"An error occurred: {e}", file=sys.stderr)


# Entry point of the script
if __name__ == '__main__':
    main()
