import sys
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
import plotly.graph_objs as go
import plotly.offline as py


class PlotlyWebview(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Plotly Test")
        self.setGeometry(5, 30, 1355, 730)
        layout = QVBoxLayout()
        self.browser = QWebEngineView()
        layout.addWidget(self.browser)
        self.setLayout(layout)

        # Create a simple Plotly graph
        fig = go.Figure(data=[go.Scatter(x=[1, 2, 3], y=[4, 1, 2])])
        html_file = 'temp_plot.html'
        py.plot(fig, filename=html_file, auto_open=False)

        # Load the Plotly graph in QWebEngineView
        self.browser.setUrl(f'file:///{os.path.abspath(html_file)}')


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = PlotlyWebview()
    win.show()
    sys.exit(app.exec_())
