import sys
import os
import pandas as pd
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QApplication, QCheckBox, QDateEdit, \
    QPushButton
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import Qt, QUrl, QDate
import plotly.graph_objs as go
import plotly.offline as py

# Dictionary mapping stock tickers to their full names
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


class FocusView(QWidget):
    def __init__(self, parent=None):
        super(FocusView, self).__init__(parent)
        self.setWindowTitle("Focus View")
        self.resize(1200, 800)

        # Main layout setup
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Top layout for ComboBoxes
        top_layout = QHBoxLayout()
        top_layout.setSpacing(5)
        top_layout.setContentsMargins(5, 5, 5, 5)

        self.combo_box = QComboBox(self)
        top_layout.addWidget(self.combo_box)

        self.chart_type_combo = QComboBox(self)
        self.chart_type_combo.addItems(["Line Chart", "Candlestick Chart"])
        top_layout.addWidget(self.chart_type_combo)

        self.timeframe_combo = QComboBox(self)
        self.timeframe_combo.addItems(
            ["YTD", "Past 10 Years", "Past 5 Years", "Past Year", "Monthly", "Quarterly", "Weekly", "Custom"])
        top_layout.addWidget(self.timeframe_combo)

        self.start_date_edit = QDateEdit(self)
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.start_date_edit.setDate(QDate.currentDate().addYears(-1))
        top_layout.addWidget(self.start_date_edit)

        self.end_date_edit = QDateEdit(self)
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDisplayFormat('yyyy-MM-dd')
        self.end_date_edit.setDate(QDate.currentDate())
        top_layout.addWidget(self.end_date_edit)

        self.update_button = QPushButton('Update', self)
        self.update_button.clicked.connect(self.on_custom_date_update)
        top_layout.addWidget(self.update_button)

        self.combo_box.currentIndexChanged.connect(self.on_stock_change)
        self.chart_type_combo.currentIndexChanged.connect(self.on_stock_change)
        self.timeframe_combo.currentIndexChanged.connect(self.on_timeframe_change)

        self.stock_label = QLabel("Select a stock to display", self)
        self.stock_label.setFixedHeight(30)
        top_layout.addWidget(self.stock_label)

        main_layout.addLayout(top_layout)

        # Checkboxes for financial indicators
        indicators_layout = QHBoxLayout()
        indicators_layout.setSpacing(10)
        indicators_layout.setContentsMargins(5, 5, 5, 5)

        self.indicator_checkboxes = {
            'MA': QCheckBox('Simple Moving Average (SMA)', self),
            'EMA': QCheckBox('Exponential MA (EMA)', self),
            'BB': QCheckBox('Bollinger Bands', self),
            'MACD': QCheckBox('MACD', self),
            'RSI': QCheckBox('Relative Strength Index (RSI)', self)
        }

        for checkbox in self.indicator_checkboxes.values():
            checkbox.stateChanged.connect(self.update_indicators)
            indicators_layout.addWidget(checkbox)

        main_layout.addLayout(indicators_layout)

        # Metrics Dashboard layout in a single row
        self.dashboard_layout = QHBoxLayout()
        self.dashboard_layout.setSpacing(5)
        self.dashboard_layout.setContentsMargins(5, 5, 5, 5)

        # Sample metrics (placeholders) with color coding and rounded corners
        self.metric_labels = {
            "Open": self.create_metric_panel("Open: -", "#5D6D7E"),
            "Close": self.create_metric_panel("Close: -", "#5B2C6F"),
            "High": self.create_metric_panel("High: -", "#A04000"),
            "Low": self.create_metric_panel("Low: -", "#1C2833"),
            "Volume": self.create_metric_panel("Volume: -", "#145A32")
        }

        for label_widget in self.metric_labels.values():
            self.dashboard_layout.addWidget(label_widget)

        main_layout.addLayout(self.dashboard_layout)

        # Web view for displaying Plotly chart
        self.web_view = QWebEngineView(self)
        main_layout.addWidget(self.web_view)

        self.setLayout(main_layout)

        # Chart type and timeframe state
        self.chart_type = 'line'
        self.timeframe = 'Past Year'

        # Load stock data in the background
        self.load_stock_data("stock_data")

    def create_metric_panel(self, text, bg_color):
        label = QLabel(text, self)
        label.setFixedHeight(50)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(f"""
            background-color: {bg_color};
            color: white;
            border: 1px solid black;
            padding: 5px;
            border-radius: 10px;
        """)
        return label

    def load_stock_data(self, data_directory):
        self.stock_data = {}
        try:
            for filename in os.listdir(data_directory):
                if filename.endswith("_data.csv"):
                    ticker = filename.split('_')[0]
                    file_path = os.path.join(data_directory, filename)
                    df = pd.read_csv(file_path, parse_dates=['Date'], index_col='Date')
                    if ticker in stock_full_names:
                        self.stock_data[ticker] = df

            self.combo_box.addItems(self.get_stock_list())
            self.combo_box.setCurrentIndex(0)
            self.on_stock_change()
        except Exception as e:
            print(f"Error loading data: {e}")

    def get_stock_list(self):
        return [f"{stock_full_names[ticker]} ({ticker})" for ticker in self.stock_data.keys()]

    def on_stock_change(self):
        selected = self.combo_box.currentText()
        if selected:
            ticker = selected.split('(')[-1].strip(')')
            self.stock_label.setText(f"Showing data for: {selected}")
            self.update_chart_type_and_data(ticker)
            self.update_metrics_dashboard(ticker)

    def on_timeframe_change(self):
        selected = self.combo_box.currentText()
        if selected:
            ticker = selected.split('(')[-1].strip(')')
            self.update_chart_type_and_data(ticker)

    def on_custom_date_update(self):
        selected = self.combo_box.currentText()
        if selected:
            ticker = selected.split('(')[-1].strip(')')
            self.timeframe = 'Custom'
            self.update_chart_type_and_data(ticker)

    def update_chart_type_and_data(self, stock_symbol):
        self.chart_type = 'line' if self.chart_type_combo.currentText() == 'Line Chart' else 'candlestick'

        if stock_symbol not in self.stock_data:
            print(f"No data found for {stock_symbol}")
            return

        df = self.stock_data[stock_symbol]
        df = self.filter_data_by_timeframe(df)

        if self.chart_type == 'line':
            trace = go.Scatter(x=df.index, y=df['Close'], mode='lines', name=f'{stock_symbol} Close')
        else:
            trace = go.Candlestick(x=df.index,
                                   open=df['Open'],
                                   high=df['High'],
                                   low=df['Low'],
                                   close=df['Close'],
                                   name=f'{stock_symbol} Candlestick')

        fig = go.Figure(data=[trace])

        # Add financial indicators if selected
        for indicator, checkbox in self.indicator_checkboxes.items():
            if checkbox.isChecked():
                self.add_financial_indicator(fig, df, indicator)

        # Update layout to remove any borders/margins and set the background color
        fig.update_layout(
            margin=dict(l=20, r=20, b=20, t=60),  # Adjusted top margin for title
            paper_bgcolor="Black",
            plot_bgcolor="Black",
            title=f"{stock_full_names[stock_symbol]} ({stock_symbol}) Stock Price",
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            template='plotly_dark'  # Applying dark theme
        )

        fig.update_layout(autosize=True, hovermode='x unified')

        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(
                    visible=True
                ),
                type="date"
            )
        )

        # Ensure zoom feature is enabled for scroll wheel
        fig.update_layout(dragmode="zoom", showlegend=True)
        fig.update_yaxes(fixedrange=False)

        # Additional CSS to ensure no border/margin/padding in the HTML
        additional_css = """
        <style>
            body {
                margin: 0;
                padding: 0;
                background-color: #000000;
            }
            .plotly-graph-div {
                background-color: #000000;
            }
        </style>
        """

        # Generate the HTML content
        html_content = f"""
        <html>
        <head>{additional_css}</head>
        <body>{py.plot(fig, include_plotlyjs='cdn', output_type='div')}</body>
        </html>
        """

        html_file = 'stock_chart.html'
        with open(html_file, 'w') as file:
            file.write(html_content)

        local_url = QUrl.fromLocalFile(os.path.abspath(html_file))
        self.web_view.setUrl(local_url)

    def filter_data_by_timeframe(self, df):
        if self.timeframe_combo.currentText() == "YTD":
            return df[df.index.year == pd.to_datetime('today').year]
        if self.timeframe_combo.currentText() == "Past 10 Years":
            return df[df.index >= pd.Timestamp.now() - pd.DateOffset(years=10)]
        if self.timeframe_combo.currentText() == "Past 5 Years":
            return df[df.index >= pd.Timestamp.now() - pd.DateOffset(years=5)]
        if self.timeframe_combo.currentText() == "Past Year":
            return df[df.index >= pd.Timestamp.now() - pd.DateOffset(years=1)]
        if self.timeframe_combo.currentText() == "Monthly":
            return df[df.index >= pd.Timestamp.now() - pd.DateOffset(months=1)]
        if self.timeframe_combo.currentText() == "Quarterly":
            return df[df.index >= pd.Timestamp.now() - pd.DateOffset(months=3)]
        if self.timeframe_combo.currentText() == "Weekly":
            return df[df.index >= pd.Timestamp.now().normalize() - pd.DateOffset(weeks=1)]
        if self.timeframe == "Custom":
            start_date = self.start_date_edit.date().toPyDate()
            end_date = self.end_date_edit.date().toPyDate()
            return df[(df.index >= start_date) & (df.index <= end_date)]
        return df

    def add_financial_indicator(self, fig, df, indicator):
        if indicator == 'MA':
            df.loc[:, 'MA'] = df['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(x=df.index, y=df['MA'], mode='lines', name='Moving Average'))
        elif indicator == 'EMA':
            df.loc[:, 'EMA'] = df['Close'].ewm(span=20, adjust=False).mean()
            fig.add_trace(go.Scatter(x=df.index, y=df['EMA'], mode='lines', name='Exponential MA'))
        elif indicator == 'BB':
            df.loc[:, 'BB_high'] = df['Close'].rolling(window=20).mean() + 2 * df['Close'].rolling(window=20).std()
            df.loc[:, 'BB_low'] = df['Close'].rolling(window=20).mean() - 2 * df['Close'].rolling(window=20).std()
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_high'], mode='lines', name='BB High'))
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_low'], mode='lines', name='BB Low'))
        elif indicator == 'MACD':
            df.loc[:, 'EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
            df.loc[:, 'EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
            df.loc[:, 'MACD'] = df['EMA_12'] - df['EMA_26']
            fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], mode='lines', name='MACD'))
        elif indicator == 'RSI':
            delta = df['Close'].diff(1)
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = -delta.where(delta < 0, 0).rolling(14).mean()
            rs = gain / loss
            df.loc[:, 'RSI'] = 100 - (100 / (1 + rs))
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI'))

    def update_indicators(self):
        # Redraw the chart when indicators change
        self.on_stock_change()

    def update_metrics_dashboard(self, stock_symbol):
        if (stock_symbol is None) or (stock_symbol not in self.stock_data):
            print(f"No data found for {stock_symbol}")
            return

        df = self.stock_data[stock_symbol]
        latest_data = df.iloc[-1]

        self.metric_labels["Open"].setText(f"Open: {latest_data['Open']:.2f} USD")
        self.metric_labels["Close"].setText(f"Close: {latest_data['Close']:.2f} USD")
        self.metric_labels["High"].setText(f"High: {latest_data['High']:.2f} USD")
        self.metric_labels["Low"].setText(f"Low: {latest_data['Low']:.2f} USD")
        self.metric_labels["Volume"].setText(f"Volume: {latest_data['Volume']:.2f}")


def main():
    app = QApplication(sys.argv)
    ex = FocusView()
    ex.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
