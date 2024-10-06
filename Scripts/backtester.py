import os
import sys
import backtrader as bt
import pandas as pd
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QComboBox, QPushButton, QLabel, QMessageBox

# Directory where stock data is stored (Absolute path)
STOCK_DATA_PATH = os.path.abspath('Scripts/Stock Data')  # Absolute path resolution

# Basic strategy for Backtrader (for demo purposes)
class SimpleStrategy(bt.Strategy):
    def __init__(self):
        self.dataclose = self.datas[0].close

    def next(self):
        if not self.position:  # If no position, buy
            if self.dataclose[0] < self.dataclose[-1]:  # If price is falling
                self.buy()
        else:
            if self.dataclose[0] > self.dataclose[-1]:  # If price is rising
                self.sell()

# GUI Application
class StockBacktestApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stock Backtester")
        self.setGeometry(300, 300, 300, 200)

        # Layout
        layout = QVBoxLayout()

        # Combobox for selecting stocks
        self.combo = QComboBox(self)
        layout.addWidget(QLabel("Select a Stock:"))
        layout.addWidget(self.combo)

        # Backtest button
        self.backtest_btn = QPushButton("Backtest", self)
        self.backtest_btn.clicked.connect(self.run_backtest)
        layout.addWidget(self.backtest_btn)

        # Set the layout
        self.setLayout(layout)

        # Populate combobox with stock names
        self.load_stock_list()

    def load_stock_list(self):
        try:
            # Print the path to verify
            print(f"Looking for stock files in: {STOCK_DATA_PATH}")

            # Get all CSV files in the directory
            stock_files = [f for f in os.listdir(STOCK_DATA_PATH) if f.endswith('.csv')]
            if not stock_files:
                raise FileNotFoundError(f"No CSV files found in directory: {STOCK_DATA_PATH}")
            stock_names = [os.path.splitext(f)[0] for f in stock_files]
            self.combo.addItems(stock_names)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading stocks: {e}")

    def run_backtest(self):
        # Get selected stock
        stock_name = self.combo.currentText()
        if not stock_name:
            QMessageBox.warning(self, "No Stock Selected", "Please select a stock to backtest.")
            return

        # Full path to the stock data file
        stock_file = os.path.join(STOCK_DATA_PATH, stock_name + '_data.csv')

        try:
            # Load the stock data using Pandas
            data = pd.read_csv(stock_file, index_col='Date', parse_dates=True)

            # Convert the dataframe into a Backtrader-compatible data feed
            data_feed = bt.feeds.PandasData(dataname=data)

            # Create a Backtrader Cerebro engine
            cerebro = bt.Cerebro()

            # Add data feed to cerebro
            cerebro.adddata(data_feed)

            # Add strategy
            cerebro.addstrategy(SimpleStrategy)

            # Run the backtest
            cerebro.run()

            # Plot the result
            cerebro.plot()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error running backtest: {e}")

# Main entry point
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = StockBacktestApp()
    window.show()
    sys.exit(app.exec_())
