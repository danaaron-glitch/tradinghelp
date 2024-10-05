import os
import pandas as pd
import plotly.graph_objs as go
import plotly.offline as py
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QApplication, QFrame, QComboBox, QPushButton,
                             QDateEdit, QCheckBox, QSplitter)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, QDate
from tempfile import NamedTemporaryFile
import sys

# Assume stock_full_names is available from a shared module or dictionary
stock_full_names = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "NVDA": "NVIDIA Corporation",
    "ADBE": "Adobe Inc.",
    "INTC": "Intel Corporation",
    "JNJ": "Johnson & Johnson",
    "PFE": "Pfizer Inc.",
    "ABBV": "AbbVie Inc.",
    "MRK": "Merck & Co., Inc.",
    "TMO": "Thermo Fisher Scientific Inc.",
    "JPM": "JPMorgan Chase & Co.",
    "BAC": "Bank of America Corporation",
    "WFC": "Wells Fargo & Company",
    "C": "Citigroup Inc.",
    "GS": "The Goldman Sachs Group, Inc.",
    "XOM": "Exxon Mobil Corporation",
    "CVX": "Chevron Corporation",
    "PBR": "Petrobras",
    "BP": "BP plc",
    "TOT": "Total SE"
}

# Available timeframes
timeframes = ["1d", "5d", "1mo", "6mo", "1y"]

class StockComparisonWidget(QWidget):
    def __init__(self, parent=None):
        super(StockComparisonWidget, self).__init__(parent)
        self.setWindowTitle("Stock Comparison")
        self.resize(1200, 800)

        self.chart_type = 'line'  # Default chart type

        # Main layout setup
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Layout for stock selection
        selection_layout = QHBoxLayout()

        self.stock1_combo = QComboBox(self)
        self.stock1_combo.addItems(stock_full_names.keys())
        selection_layout.addWidget(QLabel("Select Stock 1:", self))
        selection_layout.addWidget(self.stock1_combo)

        self.stock2_combo = QComboBox(self)
        self.stock2_combo.addItems(stock_full_names.keys())
        selection_layout.addWidget(QLabel("Select Stock 2:", self))
        selection_layout.addWidget(self.stock2_combo)

        self.start_date = QDateEdit(self)
        self.start_date.setDate(QDate(2022, 1, 1))
        self.start_date.setCalendarPopup(True)
        selection_layout.addWidget(QLabel("Start Date:", self))
        selection_layout.addWidget(self.start_date)

        self.end_date = QDateEdit(self)
        self.end_date.setDate(QDate(2023, 1, 1))
        self.end_date.setCalendarPopup(True)
        selection_layout.addWidget(QLabel("End Date:", self))
        selection_layout.addWidget(self.end_date)

        self.timeframe_combo = QComboBox(self)
        self.timeframe_combo.addItems(timeframes)
        selection_layout.addWidget(QLabel("Timeframe:", self))
        selection_layout.addWidget(self.timeframe_combo)

        self.compare_button = QPushButton("Compare", self)
        self.compare_button.clicked.connect(self.on_compare_button_click)
        selection_layout.addWidget(self.compare_button)

        main_layout.addLayout(selection_layout)

        # Layout for indicators and chart type toggle
        options_layout = QHBoxLayout()

        self.ma_checkbox = QCheckBox("Moving Average (MA)", self)
        options_layout.addWidget(self.ma_checkbox)

        self.ema_checkbox = QCheckBox("Exponential Moving Average (EMA)", self)
        options_layout.addWidget(self.ema_checkbox)

        self.bollinger_checkbox = QCheckBox("Bollinger Bands", self)
        options_layout.addWidget(self.bollinger_checkbox)

        self.rsi_checkbox = QCheckBox("RSI", self)
        options_layout.addWidget(self.rsi_checkbox)

        self.chart_toggle_button = QPushButton("Toggle Chart Type", self)
        self.chart_toggle_button.clicked.connect(self.on_toggle_chart_type)
        options_layout.addWidget(self.chart_toggle_button)

        main_layout.addLayout(options_layout)

        # Splitter to hold two web views
        self.splitter = QSplitter(self)
        main_layout.addWidget(self.splitter)

        # Web view for displaying Plotly charts
        self.web_view = QWebEngineView(self)
        self.bar_chart_view = QWebEngineView(self)
        self.splitter.addWidget(self.web_view)
        self.splitter.addWidget(self.bar_chart_view)

        # Layout for metric panels
        self.metrics_layout = QVBoxLayout()
        self.metrics_layout.setSpacing(5)
        self.metrics_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.addLayout(self.metrics_layout)

        # Perform initial comparison on startup
        self.on_compare_button_click()

    def on_compare_button_click(self):
        stock1_symbol = self.stock1_combo.currentText()
        stock2_symbol = self.stock2_combo.currentText()
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        timeframe = self.timeframe_combo.currentText()
        print(
            f"Comparing {stock1_symbol} and {stock2_symbol} from {start_date} to {end_date} with timeframe {timeframe}")

        try:
            self.compare_stocks(stock1_symbol, stock2_symbol, start_date, end_date)
            self.create_stock_bar_chart()
        except Exception as e:
            print(f"Error during comparison: {e}")
            self.web_view.setHtml(f"<html><body><h2>Error: {str(e)}</h2></body></html>")
            self.bar_chart_view.setHtml(f"<html><body><h2>Error: {str(e)}</h2></body></html>")

    def load_stock_data(self, stock_symbol):
        # Use the actual path to your stock data directory here
        data_directory = os.path.join("stock_data")
        file_path = os.path.join(data_directory, f"{stock_symbol}_data.csv")
        print(f"Looking for file at: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data for {stock_symbol} not found at {file_path}.")

        try:
            data = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
            print(f"Successfully loaded data for {stock_symbol}")
            return data
        except Exception as e:
            print(f"Error loading data for {stock_symbol}: {e}")
            raise

    def filter_data_by_date_range(self, data, start_date, end_date):
        print(f"Filtering data from {start_date} to {end_date}")
        filtered_data = data[(data.index >= start_date) & (data.index <= end_date)]
        print(f"Filtered data length: {len(filtered_data)}")
        return filtered_data

    def compare_stocks(self, stock1_symbol, stock2_symbol, start_date, end_date):
        try:
            stock1_data = self.load_stock_data(stock1_symbol)
            stock2_data = self.load_stock_data(stock2_symbol)
        except FileNotFoundError as e:
            self.web_view.setHtml(f"<html><body><h2>Error: {str(e)}</h2></body></html>")
            return
        except Exception as e:
            print(f"Error during loading stock data: {e}")
            self.web_view.setHtml(f"<html><body><h2>Error: {str(e)}</h2></body></html>")
            return

        try:
            stock1_data = self.filter_data_by_date_range(stock1_data, start_date, end_date)
            stock2_data = self.filter_data_by_date_range(stock2_data, start_date, end_date)

            stock1_initial_price = stock1_data['Close'].iloc[0]
            stock1_final_price = stock1_data['Close'].iloc[-1]
            stock1_percentage_change = ((stock1_final_price - stock1_initial_price) / stock1_initial_price) * 100

            stock2_initial_price = stock2_data['Close'].iloc[0]
            stock2_final_price = stock2_data['Close'].iloc[-1]
            stock2_percentage_change = ((stock2_final_price - stock2_initial_price) / stock2_initial_price) * 100

            fig = self.plot_comparative_chart(stock1_data, stock2_data, stock1_symbol, stock2_symbol)

            self.display_plot(fig, self.web_view)
            print("Calling create_metric_panels...")
            self.create_metric_panels(stock1_initial_price, stock1_final_price, stock1_percentage_change,
                                      stock2_initial_price, stock2_final_price, stock2_percentage_change)
            print("create_metric_panels called.")

            return {
                'stock1_percentage_change': stock1_percentage_change,
                'stock2_percentage_change': stock2_percentage_change,
                'stock1_initial_price': stock1_initial_price,
                'stock1_final_price': stock1_final_price,
                'stock2_initial_price': stock2_initial_price,
                'stock2_final_price': stock2_final_price
            }
        except Exception as e:
            print(f"Error during comparison: {e}")
            self.web_view.setHtml(f"<html><body><h2>Error: {str(e)}</h2></body></html>")

    def plot_comparative_chart(self, stock1_data, stock2_data, stock1_symbol, stock2_symbol):
        if self.chart_type == 'line':
            trace_stock1 = go.Scatter(x=stock1_data.index, y=stock1_data['Close'], mode='lines',
                                      name=f'{stock1_symbol} Close')
            trace_stock2 = go.Scatter(x=stock2_data.index, y=stock2_data['Close'], mode='lines',
                                      name=f'{stock2_symbol} Close')
        else:
            trace_stock1 = go.Candlestick(x=stock1_data.index,
                                          open=stock1_data['Open'],
                                          high=stock1_data['High'],
                                          low=stock1_data['Low'],
                                          close=stock1_data['Close'],
                                          name=f'{stock1_symbol} Candlestick')
            trace_stock2 = go.Candlestick(x=stock2_data.index,
                                          open=stock2_data['Open'],
                                          high=stock2_data['High'],
                                          low=stock2_data['Low'],
                                          close=stock2_data['Close'],
                                          name=f'{stock2_symbol} Candlestick')

        fig = go.Figure(data=[trace_stock1, trace_stock2])

        if self.ma_checkbox.isChecked():
            stock1_data['MA'] = stock1_data['Close'].rolling(window=20).mean()
            stock2_data['MA'] = stock2_data['Close'].rolling(window=20).mean()
            fig.add_trace(
                go.Scatter(x=stock1_data.index, y=stock1_data['MA'], mode='lines', name=f'{stock1_symbol} MA'))
            fig.add_trace(
                go.Scatter(x=stock2_data.index, y=stock2_data['MA'], mode='lines', name=f'{stock2_symbol} MA'))

        if self.ema_checkbox.isChecked():
            stock1_data['EMA'] = stock1_data['Close'].ewm(span=20, adjust=False).mean()
            stock2_data['EMA'] = stock2_data['Close'].ewm(span=20, adjust=False).mean()
            fig.add_trace(
                go.Scatter(x=stock1_data.index, y=stock1_data['EMA'], mode='lines', name=f'{stock1_symbol} EMA'))
            fig.add_trace(
                go.Scatter(x=stock2_data.index, y=stock2_data['EMA'], mode='lines', name=f'{stock2_symbol} EMA'))

        if self.bollinger_checkbox.isChecked():
            stock1_data['BB_upper'], stock1_data['BB_lower'] = self.calculate_bollinger_bands(stock1_data['Close'])
            stock2_data['BB_upper'], stock2_data['BB_lower'] = self.calculate_bollinger_bands(stock2_data['Close'])
            fig.add_trace(go.Scatter(x=stock1_data.index, y=stock1_data['BB_upper'], mode='lines',
                                     name=f'{stock1_symbol} BB Upper'))
            fig.add_trace(go.Scatter(x=stock1_data.index, y=stock1_data['BB_lower'], mode='lines',
                                     name=f'{stock1_symbol} BB Lower'))
            fig.add_trace(go.Scatter(x=stock2_data.index, y=stock2_data['BB_upper'], mode='lines',
                                     name=f'{stock2_symbol} BB Upper'))
            fig.add_trace(go.Scatter(x=stock2_data.index, y=stock2_data['BB_lower'], mode='lines',
                                     name=f'{stock2_symbol} BB Lower'))

        if self.rsi_checkbox.isChecked():
            stock1_data['RSI'] = self.calculate_rsi(stock1_data['Close'])
            stock2_data['RSI'] = self.calculate_rsi(stock2_data['Close'])
            fig.add_trace(
                go.Scatter(x=stock1_data.index, y=stock1_data['RSI'], mode='lines', name=f'{stock1_symbol} RSI'))
            fig.add_trace(
                go.Scatter(x=stock2_data.index, y=stock2_data['RSI'], mode='lines', name=f'{stock2_symbol} RSI'))

        fig.update_layout(
            title=f"Stock Comparison: {stock1_symbol} vs {stock2_symbol}",
            xaxis_title="Date",
            yaxis_title="Price",
            template='plotly_dark',
            paper_bgcolor='black',  # Black background
            plot_bgcolor='black',  # Black plot area background
            font=dict(color='white'),  # White text
            margin=dict(l=0, r=0, t=0, b=0)  # Set all margins to zero
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

    def create_metric_panels(self, stock1_initial, stock1_final, stock1_change, stock2_initial, stock2_final,
                             stock2_change):
        # Clear existing metrics
        print("Clearing existing metrics panels...")
        while self.metrics_layout.count():
            item = self.metrics_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            if item.layout() is not None:
                self.clear_layout(item.layout())
        print("Existing metrics panels cleared.")

        panel_data = {
            "Initial Price": (stock1_initial, stock2_initial),
            "Final Price": (stock1_final, stock2_final),
            "Percentage Change": (stock1_change, stock2_change)
        }

        panel_colors = {
            "Initial Price": ("#ff9800", "#2196f3"),  # Orange, Blue
            "Final Price": ("#4caf50", "#f44336"),  # Green, Red
            "Percentage Change": ("#9c27b0", "#3f51b5")  # Purple, Indigo
        }

        for metric, (value1, value2) in panel_data.items():
            hlayout = QHBoxLayout()
            hlayout.setSpacing(5)

            metric_label = QLabel(metric, self)
            metric_label.setFrameStyle(QFrame.StyledPanel)
            metric_label.setFixedHeight(30)  # Set a fixed height for labels
            metric_label.setStyleSheet(f"""
                color: white; 
                background-color: black; 
                padding: 2px;  # Reduce padding
                border-radius: 10px;
                font-size: 12px;  # Reduce font size
            """)

            stock1_label = QLabel(f"{value1:.2f}", self)
            stock1_label.setFrameStyle(QFrame.StyledPanel)
            stock1_label.setFixedHeight(30)  # Set a fixed height for labels
            stock1_label.setStyleSheet(f"""
                color: white; 
                background-color: {panel_colors[metric][0]};
                padding: 2px;  # Reduce padding
                border-radius: 10px;
                font-size: 12px;  # Reduce font size
            """)

            stock2_label = QLabel(f"{value2:.2f}", self)
            stock2_label.setFrameStyle(QFrame.StyledPanel)
            stock2_label.setFixedHeight(30)  # Set a fixed height for labels
            stock2_label.setStyleSheet(f"""
                color: white; 
                background-color: {panel_colors[metric][1]};
                padding: 2px;  # Reduce padding
                border-radius: 10px;
                font-size: 12px;  # Reduce font size
            """)

            hlayout.addWidget(metric_label, stretch=1)
            hlayout.addWidget(stock1_label, stretch=1)
            hlayout.addWidget(stock2_label, stretch=1)

            self.metrics_layout.addLayout(hlayout)
        print("New metrics panels created.")

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def display_plot(self, fig, view):
        html_content = py.plot(fig, include_plotlyjs='cdn', output_type='div')
        with NamedTemporaryFile(delete=False, suffix=".html") as f:
            f.write(f"<html><body style='margin:0;'>{html_content}</body></html>".encode('utf-8'))
            temp_file_path = f.name

        local_url = QUrl.fromLocalFile(temp_file_path)
        print(f"Displaying plot from: {local_url.toString()}")
        view.setUrl(local_url)

    def create_stock_bar_chart(self):
        data = []
        for i, stock in enumerate(stock_full_names.keys()):
            df = self.load_stock_data(stock)
            pct_change = ((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]) * 100
            data.append(go.Bar(
                x=[stock],
                y=[pct_change],
                name=stock_full_names[stock],
                marker=dict(
                    color='rgb(55, 83, 109)'
                )
            ))

        layout = go.Layout(
            title="Percentage Change in Stock Prices",
            xaxis=dict(title='Stocks'),
            yaxis=dict(title='Percentage Change'),
            template='plotly_dark',
            paper_bgcolor='black',  # Black background
            plot_bgcolor='black',  # Black plot area background
            font=dict(color='white'),  # White text
            margin=dict(l=0, r=0, t=0, b=0)  # Set all margins to zero
        )

        fig = go.Figure(data=data, layout=layout)
        self.display_plot(fig, self.bar_chart_view)

    def on_toggle_chart_type(self):
        if self.chart_type == 'line':
            self.chart_type = 'candlestick'
        else:
            self.chart_type = 'line'

        self.on_compare_button_click()

    # Main entry point of the application
    if __name__ == "__main__":
        app = QApplication(sys.argv)
        widget = StockComparisonWidget()
        widget.show()
        sys.exit(app.exec_())
