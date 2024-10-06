import sys
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QApplication, QComboBox, QLabel, QCheckBox, QHBoxLayout, QGroupBox, \
    QButtonGroup
from PyQt5.QtWebEngineWidgets import QWebEngineView
import plotly.io as pio
from PyQt5.QtCore import QUrl
import os
import pandas as pd
import plotly.graph_objects as go
from sentanalysis import SentimentAnalysis

# List of stock tickers
stock_tickers = {
    "Technology": ["AAPL", "MSFT", "NVDA", "ADBE", "INTC"],
    "Healthcare": ["JNJ", "PFE", "ABBV", "MRK", "TMO"],
    "Finance": ["JPM", "BAC", "WFC", "C", "GS"],
    "Energy": ["XOM", "CVX", "PBR", "BP", "TOT"]
}

# Sector ETFs and actual sector names
sector_etfs = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Finance": "XLF",
    "Energy": "XLE"
}

# Directory where datafetcher stores the stock and sector data
data_dir = 'stock_data'

# List of available timeframes
timeframes = ["1M", "3M", "6M", "1Y", "YTD", "All"]

# Stock ticker to full name mapping
ticker_full_names = {
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
    "PBR": "Petróleo Brasileiro S.A. - Petrobras",
    "BP": "BP p.l.c.",
    "TOT": "TotalEnergies SE"
}


def ticker_to_full_name(ticker):
    return ticker_full_names.get(ticker, ticker)


class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super(DashboardWidget, self).__init__(parent)
        self.stock_checkboxes = {}
        self.sector_checkboxes = {}
        self.timeframe_checkboxes = {}
        self.initUI()
        self.load_dashboard()

    def initUI(self):
        self.setWindowTitle('Stock Sentiment Dashboard')
        self.setGeometry(100, 100, 1600, 1200)

        # Main layout
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        # Add sector and stock checkboxes
        main_layout.addWidget(QLabel("Select Stocks and Sectors:"))

        # Container layout for sector rows (horizontal layout)
        sector_container_layout = QHBoxLayout()

        for sector, tickers in stock_tickers.items():
            sector_group_box = QGroupBox(sector)
            sector_layout = QVBoxLayout(sector_group_box)

            # Sector checkbox
            sector_checkbox = QCheckBox(f"Select/Deselect All {sector}")
            sector_checkbox.setChecked(True)  # Default all sectors to checked
            sector_checkbox.stateChanged.connect(self.on_sector_selector_change)
            sector_layout.addWidget(sector_checkbox)
            self.sector_checkboxes[sector] = sector_checkbox

            # Stock checkboxes within sector
            self.stock_checkboxes[sector] = {}
            for ticker in tickers:
                stock_checkbox = QCheckBox(ticker)
                stock_checkbox.setChecked(True)  # Default all stocks to checked
                stock_checkbox.stateChanged.connect(self.on_stock_selector_change)
                sector_layout.addWidget(stock_checkbox)
                self.stock_checkboxes[sector][ticker] = stock_checkbox

            sector_container_layout.addWidget(sector_group_box)

        # Add timeframe selection checkboxes
        timeframe_group_box = QGroupBox("Select Timeframe")
        timeframe_layout = QVBoxLayout(timeframe_group_box)
        self.timeframe_button_group = QButtonGroup()
        self.timeframe_button_group.setExclusive(True)

        for timeframe in timeframes:
            timeframe_checkbox = QCheckBox(timeframe)
            if timeframe == "All":
                timeframe_checkbox.setChecked(True)
            self.timeframe_button_group.addButton(timeframe_checkbox)
            timeframe_checkbox.toggled.connect(self.on_timeframe_change)
            timeframe_layout.addWidget(timeframe_checkbox)
            self.timeframe_checkboxes[timeframe] = timeframe_checkbox

        sector_container_layout.addWidget(timeframe_group_box)
        main_layout.addLayout(sector_container_layout)

        # Metrics Panel Layout - reorganized into categories
        metrics_layout = QHBoxLayout()

        # Best Stocks (Per Sector) category layout
        best_stocks_group_box = QGroupBox("Best Stocks (Per Sector)")
        best_stocks_layout = QVBoxLayout(best_stocks_group_box)
        self.best_stock_labels = {
            "Best Technology Stock": QLabel(),
            "Best Healthcare Stock": QLabel(),
            "Best Finance Stock": QLabel(),
            "Best Energy Stock": QLabel()
        }

        for metric_name, label in self.best_stock_labels.items():
            label.setText(f"{metric_name}: ")
            best_stocks_layout.addWidget(label)
        metrics_layout.addWidget(best_stocks_group_box)

        # 52 Week Performance category layout
        performance_group_box = QGroupBox("52 Week Performance (High/Low)")
        performance_layout = QVBoxLayout(performance_group_box)
        self.performance_labels = {
            "Best 52 Week High": QLabel(),
            "Best 52 Week Low": QLabel(),
            "Worst 52 Week High": QLabel(),
            "Worst 52 Week Low": QLabel()
        }

        for metric_name, label in self.performance_labels.items():
            label.setText(f"{metric_name}: ")
            performance_layout.addWidget(label)
        metrics_layout.addWidget(performance_group_box)

        # Miscellaneous Metrics category layout
        misc_group_box = QGroupBox("Miscellaneous Metrics")
        misc_layout = QVBoxLayout(misc_group_box)
        self.misc_labels = {
            "Best Overall Stock": QLabel(),
            "Greatest Volume": QLabel(),
            "Best Sector": QLabel()
        }

        for metric_name, label in self.misc_labels.items():
            label.setText(f"{metric_name}: ")
            misc_layout.addWidget(label)
        metrics_layout.addWidget(misc_group_box)

        main_layout.addLayout(metrics_layout)

        # Horizontal layout for line graphs (top row)
        self.line_graph_layout = QHBoxLayout()
        main_layout.addLayout(self.line_graph_layout)

        # Plotly QWebEngineView for displaying the line graphs
        self.graph_view_stock_line = QWebEngineView()
        self.line_graph_layout.addWidget(self.graph_view_stock_line)

        self.graph_view_sector_line = QWebEngineView()
        self.line_graph_layout.addWidget(self.graph_view_sector_line)

        # Horizontal layout for sentiment graphs (bottom row)
        self.sentiment_layout = QHBoxLayout()
        main_layout.addLayout(self.sentiment_layout)

        # Plotly QWebEngineView for displaying the sentiment graphs
        self.graph_view_stock_sentiment = QWebEngineView()
        self.sentiment_layout.addWidget(self.graph_view_stock_sentiment)

        self.graph_view_sector_sentiment = QWebEngineView()
        self.sentiment_layout.addWidget(self.graph_view_sector_sentiment)

        # Apply stylesheets for rounded corners
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid gray;
                border-radius: 15px;
                padding: 10px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 3px;
            }
        """)

    def on_timeframe_change(self):
        if self.sender().isChecked():
            self.load_dashboard()

    def on_stock_selector_change(self):
        self.load_dashboard()

    def on_sector_selector_change(self):
        sector = self.sender().text().split()[-1]
        is_checked = self.sender().isChecked()
        for checkbox in self.stock_checkboxes[sector].values():
            checkbox.setChecked(is_checked)
        self.load_dashboard()

    def load_dashboard(self):
        try:
            print("Loading dashboard...")
            self.update_metrics()

            # Load and plot stock prices over time
            stock_line_fig = self.create_stock_price_figure()
            stock_line_html_content = pio.to_html(stock_line_fig, full_html=False)

            # Load and plot sector prices over time
            sector_line_fig = self.create_sector_price_figure()
            sector_line_html_content = pio.to_html(sector_line_fig, full_html=False)

            # Create temporary HTML files for the line plots
            stock_line_html_file_path = os.path.abspath('stock_line_dashboard_plot.html')
            with open(stock_line_html_file_path, 'w', encoding='utf-8') as file:
                file.write(stock_line_html_content)

            sector_line_html_file_path = os.path.abspath('sector_line_dashboard_plot.html')
            with open(sector_line_html_file_path, 'w', encoding='utf-8') as file:
                file.write(sector_line_html_content)

            # Load line plots into QWebEngineView
            self.graph_view_stock_line.setUrl(QUrl.fromLocalFile(stock_line_html_file_path))
            self.graph_view_sector_line.setUrl(QUrl.fromLocalFile(sector_line_html_file_path))

            # Generate stock sentiment figure
            selected_stocks = [ticker for sector in stock_tickers for ticker, checkbox in
                               self.stock_checkboxes[sector].items() if checkbox.isChecked()]
            stock_sentiment_scores = SentimentAnalysis.get_sentiment_scores(selected_stocks, "stock")
            stock_fig = SentimentAnalysis.plot_sentiments(stock_sentiment_scores, "Stock Sentiment Scores")
            stock_html_content = pio.to_html(stock_fig, full_html=False)

            # Generate sector sentiment figure
            selected_sectors = [sector for sector, checkbox in self.sector_checkboxes.items() if checkbox.isChecked()]
            selected_sector_etfs = {sector: sector_etfs[sector] for sector in selected_sectors}
            sector_sentiment_scores = SentimentAnalysis.get_sentiment_scores(
                [etf for etf in selected_sector_etfs.values()],
                "sector")
            sector_fig = SentimentAnalysis.plot_sentiments(sector_sentiment_scores, "Sector Sentiment Scores",
                                                           symbols_label='Sector',
                                                           replace_names={etf: sector for sector, etf in
                                                                          sector_etfs.items()})
            sector_html_content = pio.to_html(sector_fig, full_html=False)

            # Create temporary HTML files for the sentiment plots
            stock_sentiment_html_file_path = os.path.abspath('stock_sentiment_dashboard_plot.html')
            with open(stock_sentiment_html_file_path, 'w', encoding='utf-8') as file:
                file.write(stock_html_content)

            sector_sentiment_html_file_path = os.path.abspath('sector_sentiment_dashboard_plot.html')
            with open(sector_sentiment_html_file_path, 'w', encoding='utf-8') as file:
                file.write(sector_html_content)

            # Load sentiment plots into QWebEngineView
            self.graph_view_stock_sentiment.setUrl(QUrl.fromLocalFile(stock_sentiment_html_file_path))
            self.graph_view_sector_sentiment.setUrl(QUrl.fromLocalFile(sector_sentiment_html_file_path))
            print("Dashboard loaded successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")

    def create_stock_price_figure(self):
        # Create Plotly figure for stock prices
        fig = go.Figure()

        # Load and plot data for each stock
        for sector, tickers in stock_tickers.items():
            for ticker in tickers:
                if self.stock_checkboxes[sector][ticker].isChecked():
                    file_name = f'{ticker}_data.csv'
                    stock_data = self.load_data(file_name)

                    if not stock_data.empty:
                        stock_data = self.filter_by_timeframe(stock_data)  # Apply timeframe filter
                        print(f"Loaded data for {ticker}: {stock_data.shape[0]} rows")
                        # Ensure data is sorted by date
                        stock_data = stock_data.sort_values(by='Date')
                        fig.add_trace(go.Scatter(
                            x=stock_data['Date'], y=stock_data['Close'],
                            mode='lines', name=f"{ticker} (Stock)"
                        ))
                    else:
                        print(f"No data to plot for {ticker}")

        # Update the layout of the stock figure
        fig.update_layout(
            title='Stock Prices Over Time',
            xaxis_title='Date',
            yaxis_title='Price',
            template='plotly_white',
            legend_title='Legend'
        )

        return fig

    def create_sector_price_figure(self):
        # Create Plotly figure for sector prices
        fig = go.Figure()

        # Load and plot data for each sector
        for sector in sector_etfs.keys():
            if self.sector_checkboxes[sector].isChecked():
                file_name = f'{sector}_data.csv'
                sector_data = self.load_data(file_name)

                if not sector_data.empty:
                    sector_data = self.filter_by_timeframe(sector_data)  # Apply timeframe filter
                    print(f"Loaded data for {sector}: {sector_data.shape[0]} rows")
                    # Ensure data is sorted by date
                    sector_data = sector_data.sort_values(by='Date')
                    fig.add_trace(go.Scatter(
                        x=sector_data['Date'], y=sector_data['Close'],
                        mode='lines', name=f"{sector} (Sector)"
                    ))
                else:
                    print(f"No data to plot for {sector}")

        # Update the layout of the sector figure
        fig.update_layout(
            title='Sector Prices Over Time',
            xaxis_title='Date',
            yaxis_title='Price',
            template='plotly_white',
            legend_title='Legend'
        )

        return fig

    def filter_by_timeframe(self, df):
        selected_timeframe = next((timeframe for timeframe, checkbox in self.timeframe_checkboxes.items() if
                                   checkbox is not None and checkbox.isChecked()), 'All')
        if selected_timeframe == "1M":
            start_date = pd.Timestamp.now() - pd.DateOffset(months=1)
        elif selected_timeframe == "3M":
            start_date = pd.Timestamp.now() - pd.DateOffset(months=3)
        elif selected_timeframe == "6M":
            start_date = pd.Timestamp.now() - pd.DateOffset(months=6)
        elif selected_timeframe == "1Y":
            start_date = pd.Timestamp.now() - pd.DateOffset(years=1)
        elif selected_timeframe == "YTD":
            start_date = pd.Timestamp(pd.Timestamp.now().year, 1, 1)
        elif selected_timeframe == "All":
            return df  # "All" timeframe, return full data
        else:
            start_date = None

        return df[df['Date'] >= start_date] if start_date else df

    def load_data(self, file_name):
        # Construct full file path
        filepath = os.path.join(data_dir, file_name)
        if os.path.exists(filepath):
            # Load the data and parse the date column
            data = pd.read_csv(filepath, parse_dates=['Date'])
            return data
        print(f"File {filepath} not found.")
        return pd.DataFrame()

    def update_metrics(self):
        selected_stocks = [ticker for sector in stock_tickers for ticker, checkbox in
                           self.stock_checkboxes[sector].items() if checkbox.isChecked()]
        data = {ticker: self.load_data(f'{ticker}_data.csv') for ticker in selected_stocks}

        if not data:
            print("No data available to calculate metrics")
            return

        processed_data = []
        greatest_volumes = []

        sector_performances = {sector: [] for sector in stock_tickers}

        for ticker, df in data.items():
            if df.empty:
                continue
            df_filtered = self.filter_by_timeframe(df)
            high_52_week = df_filtered['Close'].max()
            low_52_week = df_filtered['Close'].min()
            latest_close = df_filtered['Close'].iloc[-1] if not df_filtered.empty else None
            total_volume = df_filtered['Volume'].sum() if 'Volume' in df_filtered.columns else None
            processed_data.append((ticker, latest_close, high_52_week, low_52_week, total_volume))

            for sector, tickers in stock_tickers.items():
                if ticker in tickers:
                    sector_performances[sector].append((ticker, latest_close))

        if not processed_data:
            print("No processed data available to calculate metrics")
            return

        best_stock = max(processed_data, key=lambda x: x[1])
        best_52_week_high = max(processed_data, key=lambda x: x[2])
        best_52_week_low = max(processed_data, key=lambda x: x[3])
        worst_52_week_high = min(processed_data, key=lambda x: x[2])
        worst_52_week_low = min(processed_data, key=lambda x: x[3])
        best_overall_stock = max(processed_data, key=lambda x: (x[1], x[2]))  # Best by latest close or 52-week high
        greatest_volume_stock = max(processed_data, key=lambda x: x[4])  # Stock with greatest volume
        best_sector = max(sector_etfs.keys(), key=lambda sector: sum(
            perf[1] for perf in sector_performances[sector] if perf[1] is not None))  # Sum of latest closes

        best_tech_stock = max(sector_performances['Technology'], key=lambda x: x[1], default=(None, None))
        best_healthcare_stock = max(sector_performances['Healthcare'], key=lambda x: x[1], default=(None, None))
        best_finance_stock = max(sector_performances['Finance'], key=lambda x: x[1], default=(None, None))
        best_energy_stock = max(sector_performances['Energy'], key=lambda x: x[1], default=(None, None))

        self.best_stock_labels["Best Technology Stock"].setText(
            f"Technology: {best_tech_stock[0]} (Full Name: {ticker_to_full_name(best_tech_stock[0])}) - ${best_tech_stock[1]:.2f} USD"
            if best_tech_stock[0] else 'N/A'
        )
        self.best_stock_labels["Best Healthcare Stock"].setText(
            f"Healthcare: {best_healthcare_stock[0]} (Full Name: {ticker_to_full_name(best_healthcare_stock[0])}) - ${best_healthcare_stock[1]:.2f} USD"
            if best_healthcare_stock[0] else 'N/A'
        )
        self.best_stock_labels["Best Finance Stock"].setText(
            f"Finance: {best_finance_stock[0]} (Full Name: {ticker_to_full_name(best_finance_stock[0])}) - ${best_finance_stock[1]:.2f} USD"
            if best_finance_stock[0] else 'N/A'
        )
        self.best_stock_labels["Best Energy Stock"].setText(
            f"Energy: {best_energy_stock[0]} (Full Name: {ticker_to_full_name(best_energy_stock[0])}) - ${best_energy_stock[1]:.2f} USD"
            if best_energy_stock[0] else 'N/A'
        )

        self.performance_labels["Best 52 Week High"].setText(
            f"Best 52 Week High: {best_52_week_high[0]} (Full Name: {ticker_to_full_name(best_52_week_high[0])}) - ${best_52_week_high[2]:.2f} USD"
        )
        self.performance_labels["Best 52 Week Low"].setText(
            f"Best 52 Week Low: {best_52_week_low[0]} (Full Name: {ticker_to_full_name(best_52_week_low[0])}) - ${best_52_week_low[3]:.2f} USD"
        )
        self.performance_labels["Worst 52 Week High"].setText(
            f"Worst 52 Week High: {worst_52_week_high[0]} (Full Name: {ticker_to_full_name(worst_52_week_high[0])}) - ${worst_52_week_high[2]:.2f} USD"
        )
        self.performance_labels["Worst 52 Week Low"].setText(
            f"Worst 52 Week Low: {worst_52_week_low[0]} (Full Name: {ticker_to_full_name(worst_52_week_low[0])}) - ${worst_52_week_low[3]:.2f} USD"
        )
        self.misc_labels["Best Overall Stock"].setText(
            f"Best Overall Stock: {best_overall_stock[0]} (Full Name: {ticker_to_full_name(best_overall_stock[0])}) - ${best_overall_stock[1]:.2f} USD"
        )
        self.misc_labels["Greatest Volume"].setText(
            f"Greatest Volume: {greatest_volume_stock[0]} (Full Name: {ticker_to_full_name(greatest_volume_stock[0])}) - {greatest_volume_stock[4]:,} shares"
        )
        self.misc_labels["Best Sector"].setText(
            f"Best Sector: {best_sector} - ${sum(perf[1] for perf in sector_performances[best_sector] if perf[1] is not None):.2f} USD"
        )

        def main():
            app = QApplication(sys.argv)
            dashboard = DashboardWidget()
            dashboard.show()
            sys.exit(app.exec_())

        if __name__ == "__main__":
            main()
