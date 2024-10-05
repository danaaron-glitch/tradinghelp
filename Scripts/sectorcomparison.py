import os
import pandas as pd
import plotly.graph_objs as go
import plotly.offline as py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame, QApplication, QComboBox,
                             QPushButton, QDateEdit, QCheckBox, QHBoxLayout)  # Added QHBoxLayout here
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QDate
from tempfile import NamedTemporaryFile
import sys

# Sectors and their corresponding ETF symbols
sector_data_files = {
    "Technology": "Technology_data.csv",
    "Healthcare": "Healthcare_data.csv",
    "Finance": "Finance_data.csv",
    "Energy": "Energy_data.csv"
}


class SectorComparisonWidget(QWidget):
    def __init__(self, parent=None):
        super(SectorComparisonWidget, self).__init__(parent)
        self.setWindowTitle("Sector Comparison")
        self.resize(1200, 800)
        self.chart_type = 'line'  # Default chart type

        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Layout for sector selection and dates
        selection_layout = QGridLayout()

        sector1_label = QLabel("Select Sector 1:", self)
        self.sector1_combo = QComboBox(self)
        self.sector1_combo.addItems(sector_data_files.keys())
        self.sector1_combo.currentIndexChanged.connect(self.on_option_change)

        sector2_label = QLabel("Select Sector 2:", self)
        self.sector2_combo = QComboBox(self)
        self.sector2_combo.addItems(sector_data_files.keys())
        self.sector2_combo.currentIndexChanged.connect(self.on_option_change)

        start_date_label = QLabel("Start Date:", self)
        self.start_date = QDateEdit(self)
        self.start_date.setDate(QDate(2022, 1, 1))
        self.start_date.setCalendarPopup(True)
        self.start_date.dateChanged.connect(self.on_option_change)

        end_date_label = QLabel("End Date:", self)
        self.end_date = QDateEdit(self)
        self.end_date.setDate(QDate(2023, 1, 1))
        self.end_date.setCalendarPopup(True)
        self.end_date.dateChanged.connect(self.on_option_change)

        selection_layout.addWidget(sector1_label, 0, 0)
        selection_layout.addWidget(self.sector1_combo, 0, 1)
        selection_layout.addWidget(sector2_label, 1, 0)
        selection_layout.addWidget(self.sector2_combo, 1, 1)
        selection_layout.addWidget(start_date_label, 0, 2)
        selection_layout.addWidget(self.start_date, 0, 3)
        selection_layout.addWidget(end_date_label, 1, 2)
        selection_layout.addWidget(self.end_date, 1, 3)

        main_layout.addLayout(selection_layout)

        # Layout for indicators and chart type toggle
        options_layout = QGridLayout()

        self.ma_checkbox = QCheckBox("Moving Average (MA)", self)
        self.ma_checkbox.stateChanged.connect(self.on_option_change)
        options_layout.addWidget(self.ma_checkbox, 0, 0)

        self.ema_checkbox = QCheckBox("Exponential Moving Average (EMA)", self)
        self.ema_checkbox.stateChanged.connect(self.on_option_change)
        options_layout.addWidget(self.ema_checkbox, 0, 1)

        self.bollinger_checkbox = QCheckBox("Bollinger Bands", self)
        self.bollinger_checkbox.stateChanged.connect(self.on_option_change)
        options_layout.addWidget(self.bollinger_checkbox, 0, 2)

        self.rsi_checkbox = QCheckBox("RSI", self)
        self.rsi_checkbox.stateChanged.connect(self.on_option_change)
        options_layout.addWidget(self.rsi_checkbox, 0, 3)

        self.chart_toggle_button = QPushButton("Toggle Chart Type", self)
        self.chart_toggle_button.clicked.connect(self.on_toggle_chart_type)
        options_layout.addWidget(self.chart_toggle_button, 0, 4)

        main_layout.addLayout(options_layout)

        # Web view for displaying Plotly chart
        self.web_view = QWebEngineView(self)
        main_layout.addWidget(self.web_view)

        # Layout for metric panels
        self.metrics_layout = QVBoxLayout()
        self.metrics_layout.setSpacing(5)
        self.metrics_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addLayout(self.metrics_layout)

        # Perform initial comparison on startup
        self.on_option_change()

    def on_option_change(self):
        sector1_symbol = self.sector1_combo.currentText()
        sector2_symbol = self.sector2_combo.currentText()
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        print(f"Comparing {sector1_symbol} and {sector2_symbol} from {start_date} to {end_date}")

        try:
            self.compare_sectors(sector1_symbol, sector2_symbol, start_date, end_date)
        except Exception as e:
            print(f"Error during comparison: {e}")
            self.web_view.setHtml(f"<html><body><h2>Error: {str(e)}</h2></body></html>")

    def load_sector_data(self, sector_symbol):
        data_directory = os.path.join(os.path.dirname(__file__), "stock_data")
        file_path = os.path.join(data_directory, sector_data_files[sector_symbol])
        print(f"Looking for file at: {file_path}")  # Debug print statement
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data for {sector_symbol} not found at {file_path}.")

        print(f"Absolute path: {os.path.abspath(file_path)}")  # Debug print statement

        try:
            data = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
            print(f"Successfully loaded data for {sector_symbol}")
            return data
        except Exception as e:
            print(f"Error loading data for {sector_symbol}: {e}")
            raise

    def filter_data_by_date_range(self, data, start_date, end_date):
        print(f"Filtering data from {start_date} to {end_date}")
        filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]
        print(f"Filtered data length: {len(filtered_data)}")
        return filtered_data

    def compare_sectors(self, sector1_symbol, sector2_symbol, start_date, end_date):
        try:
            sector1_data = self.load_sector_data(sector1_symbol)
            sector2_data = self.load_sector_data(sector2_symbol)
        except FileNotFoundError as e:
            self.web_view.setHtml(f"<html><body><h2>Error: {str(e)}</h2></body></html>")
            return
        except Exception as e:
            print(f"Error during loading sector data: {e}")
            self.web_view.setHtml(f"<html><body><h2>Error: {str(e)}</h2></body></html>")
            return

        try:
            sector1_data = self.filter_data_by_date_range(sector1_data, start_date, end_date)
            sector2_data = self.filter_data_by_date_range(sector2_data, start_date, end_date)

            sector1_initial_price = sector1_data['Close'].iloc[0]
            sector1_final_price = sector1_data['Close'].iloc[-1]
            sector1_percentage_change = ((sector1_final_price - sector1_initial_price) / sector1_initial_price) * 100

            sector2_initial_price = sector2_data['Close'].iloc[0]
            sector2_final_price = sector2_data['Close'].iloc[-1]
            sector2_percentage_change = ((sector2_final_price - sector2_initial_price) / sector2_initial_price) * 100

            fig = self.plot_comparative_chart(sector1_data, sector2_data, sector1_symbol, sector2_symbol)

            self.display_plot(fig)
            self.create_metric_panels(sector1_initial_price, sector1_final_price, sector1_percentage_change,
                                      sector2_initial_price, sector2_final_price, sector2_percentage_change)

            return {
                'sector1_percentage_change': sector1_percentage_change,
                'sector2_percentage_change': sector2_percentage_change,
                'sector1_initial_price': sector1_initial_price,
                'sector1_final_price': sector1_final_price,
                'sector2_initial_price': sector2_initial_price,
                'sector2_final_price': sector2_final_price
            }
        except Exception as e:
            print(f"Error during comparison: {e}")
            self.web_view.setHtml(f"<html><body><h2>Error: {str(e)}</h2></body></html>")

    def plot_comparative_chart(self, sector1_data, sector2_data, sector1_symbol, sector2_symbol):
        if self.chart_type == 'line':
            trace_sector1 = go.Scatter(x=sector1_data.index, y=sector1_data['Close'], mode='lines',
                                       name=f'{sector1_symbol} Close')
            trace_sector2 = go.Scatter(x=sector2_data.index, y=sector2_data['Close'], mode='lines',
                                       name=f'{sector2_symbol} Close')
        else:
            trace_sector1 = go.Candlestick(x=sector1_data.index,
                                           open=sector1_data['Open'], high=sector1_data['High'],
                                           low=sector1_data['Low'], close=sector1_data['Close'],
                                           name=f'{sector1_symbol} Candlestick')
            trace_sector2 = go.Candlestick(x=sector2_data.index,
                                           open=sector2_data['Open'], high=sector2_data['High'],
                                           low=sector2_data['Low'], close=sector2_data['Close'],
                                           name=f'{sector2_symbol} Candlestick')

        fig = go.Figure(data=[trace_sector1, trace_sector2])

        if self.ma_checkbox.isChecked():
            sector1_data['MA'] = sector1_data['Close'].rolling(window=20).mean()
            sector2_data['MA'] = sector2_data['Close'].rolling(window=20).mean()
            fig.add_trace(
                go.Scatter(x=sector1_data.index, y=sector1_data['MA'], mode='lines', name=f'{sector1_symbol} MA'))
            fig.add_trace(
                go.Scatter(x=sector2_data.index, y=sector2_data['MA'], mode='lines', name=f'{sector2_symbol} MA'))

        if self.ema_checkbox.isChecked():
            sector1_data['EMA'] = sector1_data['Close'].ewm(span=20, adjust=False).mean()
            sector2_data['EMA'] = sector2_data['Close'].ewm(span=20, adjust=False).mean()
            fig.add_trace(
                go.Scatter(x=sector1_data.index, y=sector1_data['EMA'], mode='lines', name=f'{sector1_symbol} EMA'))
            fig.add_trace(
                go.Scatter(x=sector2_data.index, y=sector2_data['EMA'], mode='lines', name=f'{sector2_symbol} EMA'))

        if self.bollinger_checkbox.isChecked():
            sector1_data['BB_upper'], sector1_data['BB_lower'] = self.calculate_bollinger_bands(sector1_data['Close'])
            sector2_data['BB_upper'], sector2_data['BB_lower'] = self.calculate_bollinger_bands(sector2_data['Close'])
            fig.add_trace(go.Scatter(x=sector1_data.index, y=sector1_data['BB_upper'], mode='lines',
                                     name=f'{sector1_symbol} BB Upper'))
            fig.add_trace(go.Scatter(x=sector1_data.index, y=sector1_data['BB_lower'], mode='lines',
                                     name=f'{sector1_symbol} BB Lower'))
            fig.add_trace(go.Scatter(x=sector2_data.index, y=sector2_data['BB_upper'], mode='lines',
                                     name=f'{sector2_symbol} BB Upper'))
            fig.add_trace(go.Scatter(x=sector2_data.index, y=sector2_data['BB_lower'], mode='lines',
                                     name=f'{sector2_symbol} BB Lower'))

        if self.rsi_checkbox.isChecked():
            sector1_data['RSI'] = self.calculate_rsi(sector1_data['Close'])
            sector2_data['RSI'] = self.calculate_rsi(sector2_data['Close'])
            fig.add_trace(
                go.Scatter(x=sector1_data.index, y=sector1_data['RSI'], mode='lines', name=f'{sector1_symbol} RSI'))
            fig.add_trace(
                go.Scatter(x=sector2_data.index, y=sector2_data['RSI'], mode='lines', name=f'{sector2_symbol} RSI'))

        fig.update_layout(
            title=f"Sector Comparison: {sector1_symbol} vs {sector2_symbol}",
            xaxis_title="Date",
            yaxis_title="Price",
            template='plotly_dark',
            paper_bgcolor='black',
            plot_bgcolor='black',
            font=dict(color='white'),
            margin=dict(l=20, r=20, t=60, b=20)  # Adjusted margins
        )

        return fig

    def calculate_bollinger_bands(self, series, window=20):
        """Calculate Bollinger Bands."""
        rolling_mean = series.rolling(window).mean()
        rolling_std = series.rolling(window).std()
        upper_band = rolling_mean + (rolling_std * 2)
        lower_band = rolling_mean - (rolling_std * 2)
        return upper_band, lower_band

    def calculate_rsi(self, series, window=14):
        """Calculate Relative Strength Index (RSI)."""
        delta = series.diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)

        avg_gain = gain.rolling(window).mean()
        avg_loss = loss.rolling(window).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def create_metric_panels(self, sector1_initial, sector1_final, sector1_change, sector2_initial, sector2_final,
                             sector2_change):
        while self.metrics_layout.count():
            item = self.metrics_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            if item.layout() is not None:
                self.clear_layout(item.layout())

        panel_data = {
            "Initial Price": (sector1_initial, sector2_initial),
            "Final Price": (sector1_final, sector2_final),
            "Percentage Change": (sector1_change, sector2_change)
        }

        panel_colors = {
            "Initial Price": ("#ff9800", "#2196f3"),
            "Final Price": ("#4caf50", "#f44336"),
            "Percentage Change": ("#9c27b0", "#3f51b5")
        }

        for metric, (value1, value2) in panel_data.items():
            hlayout = QHBoxLayout()
            hlayout.setSpacing(5)

            metric_label = QLabel(metric, self)
            metric_label.setFrameStyle(QFrame.StyledPanel)
            metric_label.setFixedHeight(30)
            metric_label.setStyleSheet(f"""
                color: white; 
                background-color: black; 
                padding: 2px;
                border-radius: 10px;
                font-size: 12px;
            """)

            sector1_label = QLabel(f"{value1:.2f}", self)
            sector1_label.setFrameStyle(QFrame.StyledPanel)
            sector1_label.setFixedHeight(30)
            sector1_label.setStyleSheet(f"""
                color: white; 
                background-color: {panel_colors[metric][0]};
                padding: 2px;
                border-radius: 10px;
                font-size: 12px;
            """)

            sector2_label = QLabel(f"{value2:.2f}", self)
            sector2_label.setFrameStyle(QFrame.StyledPanel)
            sector2_label.setFixedHeight(30)
            sector2_label.setStyleSheet(f"""
                color: white; 
                background-color: {panel_colors[metric][1]};
                padding: 2px;
                border-radius: 10px;
                font-size: 12px;
            """)

            hlayout.addWidget(metric_label, stretch=1)
            hlayout.addWidget(sector1_label, stretch=1)
            hlayout.addWidget(sector2_label, stretch=1)

            self.metrics_layout.addLayout(hlayout)
        print("New metrics panels created.")

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def display_plot(self, fig):
        # Generate the HTML content for the Plotly figure
        html_content = py.plot(fig, include_plotlyjs='cdn', output_type='div')

        # Create a NamedTemporaryFile to store the HTML content
        with NamedTemporaryFile(delete=False, suffix=".html") as f:
            f.write(f"<html><body style='margin: 0; padding: 0;'>{html_content}</body></html>".encode('utf-8'))
            temp_file_path = f.name

        # Load the temporary HTML file in the QWebEngineView
        self.web_view.load(QUrl.fromLocalFile(temp_file_path))

        # Optionally, store the temporary file path for cleanup if needed
        self.temp_file_path = temp_file_path

    def on_toggle_chart_type(self):
        self.chart_type = 'candlestick' if self.chart_type == 'line' else 'line'
        self.on_option_change()  # Refresh the chart upon toggling


# Only needed if running the file directly
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = SectorComparisonWidget()
    window.show()
    sys.exit(app.exec_())
