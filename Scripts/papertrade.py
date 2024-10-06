import sys
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox, QFormLayout, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtWebEngineWidgets import QWebEngineView


class PaperTradingSimulator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Paper Trading Simulator")
        self.setGeometry(100, 100, 1400, 800)

        # Initial balance and portfolio setup
        self.cash_balance = 100000  # Starting with $100,000
        self.portfolio = {}  # Holds stocks with {symbol: (quantity, avg_buy_price)}
        self.trades = []  # To store all trade records

        # Main widget and layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        main_layout = QHBoxLayout(self.main_widget)

        # Sidebar for portfolio and cash balance
        sidebar_layout = QVBoxLayout()

        # Cash balance display
        self.cash_label = QLabel(f"Cash Balance: ${self.cash_balance:,.2f}")
        self.cash_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        sidebar_layout.addWidget(self.cash_label)

        # Portfolio table
        self.portfolio_table = QTableWidget(0, 3)
        self.portfolio_table.setHorizontalHeaderLabels(["Stock", "Quantity", "Price"])
        self.portfolio_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        sidebar_layout.addWidget(self.portfolio_table)

        # Add sidebar to the main layout
        main_layout.addLayout(sidebar_layout, 1)

        # Main content area: stock chart and portfolio value
        content_layout = QVBoxLayout()

        # Stock chart (Plotly in QWebEngineView)
        self.stock_chart_view = QWebEngineView()
        content_layout.addWidget(self.stock_chart_view)

        # Portfolio value chart (Plotly in QWebEngineView)
        self.portfolio_value_view = QWebEngineView()
        content_layout.addWidget(self.portfolio_value_view)

        # Add content layout to the main layout
        main_layout.addLayout(content_layout, 3)

        # Trading panel (for placing orders)
        trading_layout = QVBoxLayout()

        # Stock selection and order form
        form_layout = QFormLayout()
        self.stock_selector = QComboBox()
        self.stock_selector.addItems(["AAPL", "MSFT", "NVDA", "GOOGL", "META", "JNJ", "PFE", "MRK", "ABBV", "LLY",
                                      "JPM", "BAC", "WFC", "C", "GS", "AMZN", "TSLA", "HD", "MCD", "NKE"])

        self.order_type_selector = QComboBox()
        self.order_type_selector.addItems(["Market Order", "Limit Order"])

        self.quantity_spinbox = QSpinBox()
        self.quantity_spinbox.setMinimum(1)

        self.limit_price_spinbox = QDoubleSpinBox()
        self.limit_price_spinbox.setMinimum(1)
        self.limit_price_spinbox.setVisible(False)  # Hide limit price unless 'Limit Order' selected

        # Show limit price if 'Limit Order' is selected
        self.order_type_selector.currentIndexChanged.connect(self.toggle_limit_price)

        form_layout.addRow("Stock:", self.stock_selector)
        form_layout.addRow("Order Type:", self.order_type_selector)
        form_layout.addRow("Quantity:", self.quantity_spinbox)
        form_layout.addRow("Limit Price:", self.limit_price_spinbox)

        trading_layout.addLayout(form_layout)

        # Buy/Sell Buttons
        buy_button = QPushButton("Buy")
        buy_button.clicked.connect(self.buy_stock)
        sell_button = QPushButton("Sell")
        sell_button.clicked.connect(self.sell_stock)
        trading_layout.addWidget(buy_button)
        trading_layout.addWidget(sell_button)

        # Transaction History Table
        self.transaction_table = QTableWidget(0, 4)
        self.transaction_table.setHorizontalHeaderLabels(["Action", "Stock", "Quantity", "Price"])
        self.transaction_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        trading_layout.addWidget(self.transaction_table)

        # Add trading layout to main layout
        main_layout.addLayout(trading_layout, 2)

        # Dashboard section for trade statistics
        self.dashboard_layout = QVBoxLayout()

        # Add labels for statistics
        self.total_pnl_label = QLabel("Total PnL: $0.00")
        self.win_loss_ratio_label = QLabel("Win/Loss Ratio: 0.00")
        self.percentage_return_label = QLabel("Percentage Return: 0.00%")
        self.total_wins_label = QLabel("Winning Trades: 0")
        self.total_losses_label = QLabel("Losing Trades: 0")

        for label in [self.total_pnl_label, self.win_loss_ratio_label, self.percentage_return_label,
                      self.total_wins_label, self.total_losses_label]:
            label.setStyleSheet("font-size: 16px; font-weight: bold;")

        # Add labels to the dashboard layout
        self.dashboard_layout.addWidget(self.total_pnl_label)
        self.dashboard_layout.addWidget(self.win_loss_ratio_label)
        self.dashboard_layout.addWidget(self.percentage_return_label)
        self.dashboard_layout.addWidget(self.total_wins_label)
        self.dashboard_layout.addWidget(self.total_losses_label)

        # Add the dashboard layout to the sidebar layout
        sidebar_layout.addLayout(self.dashboard_layout)

        # Load initial data and charts
        self.update_stock_chart()
        self.update_portfolio_value_chart()

    def toggle_limit_price(self):
        """ Show or hide limit price input based on order type. """
        if self.order_type_selector.currentText() == "Limit Order":
            self.limit_price_spinbox.setVisible(True)
        else:
            self.limit_price_spinbox.setVisible(False)

    def buy_stock(self):
        """ Execute a buy order for the selected stock. """
        stock = self.stock_selector.currentText()
        quantity = self.quantity_spinbox.value()

        # Get the current price (using yfinance)
        price = self.get_stock_price(stock)

        # If it's a limit order, use the limit price
        if self.order_type_selector.currentText() == "Limit Order":
            price = self.limit_price_spinbox.value()

        # Calculate total cost and check if there's enough cash
        total_cost = price * quantity
        if total_cost > self.cash_balance:
            print("Not enough cash!")
            return

        # Update cash balance
        self.cash_balance -= total_cost
        self.cash_label.setText(f"Cash Balance: ${self.cash_balance:,.2f}")

        # Add stock to portfolio or update existing stock quantity
        if stock in self.portfolio:
            current_quantity, avg_price = self.portfolio[stock]
            new_quantity = current_quantity + quantity
            new_avg_price = ((current_quantity * avg_price) + (quantity * price)) / new_quantity
            self.portfolio[stock] = (new_quantity, new_avg_price)
        else:
            self.portfolio[stock] = (quantity, price)

        # Add to transaction history
        self.add_transaction("Buy", stock, quantity, price)

        # Record the trade
        self.record_trade("Buy", stock, quantity, price)

        # Update portfolio table and charts
        self.update_portfolio_table()
        self.update_portfolio_value_chart()

        # Update dashboard statistics
        self.update_dashboard()

    def sell_stock(self):
        """ Execute a sell order for the selected stock. """
        stock = self.stock_selector.currentText()
        quantity = self.quantity_spinbox.value()

        # Check if user holds enough stock to sell
        if stock not in self.portfolio or self.portfolio[stock][0] < quantity:
            print("Not enough stock to sell!")
            return

        # Get the current price (using yfinance)
        price = self.get_stock_price(stock)

        # If it's a limit order, use the limit price
        if self.order_type_selector.currentText() == "Limit Order":
            price = self.limit_price_spinbox.value()

        # Calculate total sale value
        total_value = price * quantity

        # Update cash balance
        self.cash_balance += total_value
        self.cash_label.setText(f"Cash Balance: ${self.cash_balance:,.2f}")

        # Update stock quantity in the portfolio
        current_quantity, avg_price = self.portfolio[stock]
        new_quantity = current_quantity - quantity
        if new_quantity == 0:
            del self.portfolio[stock]
        else:
            self.portfolio[stock] = (new_quantity, avg_price)

        # Add to transaction history
        self.add_transaction("Sell", stock, quantity, price)

        # Record the trade
        self.record_trade("Sell", stock, quantity, sell_price=price)

        # Update portfolio table and charts
        self.update_portfolio_table()
        self.update_portfolio_value_chart()

        # Update dashboard statistics
        self.update_dashboard()

    def get_stock_price(self, stock):
        """ Fetch the current stock price from yfinance. """
        ticker = yf.Ticker(stock)
        stock_data = ticker.history(period="1d")
        return stock_data["Close"][-1]

    def add_transaction(self, action, stock, quantity, price):
        """ Add a transaction to the transaction history table. """
        row_position = self.transaction_table.rowCount()
        self.transaction_table.insertRow(row_position)
        self.transaction_table.setItem(row_position, 0, QTableWidgetItem(action))
        self.transaction_table.setItem(row_position, 1, QTableWidgetItem(stock))
        self.transaction_table.setItem(row_position, 2, QTableWidgetItem(str(quantity)))
        self.transaction_table.setItem(row_position, 3, QTableWidgetItem(f"${price:,.2f}"))

    def update_portfolio_table(self):
        """ Update the portfolio table with the current stock holdings. """
        self.portfolio_table.setRowCount(0)  # Clear the table
        for stock, (quantity, price) in self.portfolio.items():
            row_position = self.portfolio_table.rowCount()
            self.portfolio_table.insertRow(row_position)
            self.portfolio_table.setItem(row_position, 0, QTableWidgetItem(stock))
            self.portfolio_table.setItem(row_position, 1, QTableWidgetItem(str(quantity)))
            self.portfolio_table.setItem(row_position, 2, QTableWidgetItem(f"${price:,.2f}"))

    def update_stock_chart(self):
        """ Plot the stock chart using Plotly. """
        stock = self.stock_selector.currentText()
        stock_data = yf.Ticker(stock).history(period="1mo")

        fig = go.Figure()
        fig.add_trace(go.Candlestick(x=stock_data.index,
                                     open=stock_data['Open'],
                                     high=stock_data['High'],
                                     low=stock_data['Low'],
                                     close=stock_data['Close'],
                                     name="Candlestick"))

        fig.update_layout(title=f"{stock} Stock Price",
                          xaxis_title="Date",
                          yaxis_title="Price (USD)")

        self.display_plot(fig, self.stock_chart_view)

    def update_portfolio_value_chart(self):
        """ Plot the portfolio value chart using Plotly. """
        portfolio_value = self.cash_balance + sum(quantity * self.get_stock_price(stock)
                                                  for stock, (quantity, _) in self.portfolio.items())

        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode="gauge+number",
            value=portfolio_value,
            title={'text': "Portfolio Value"},
            gauge={'axis': {'range': [None, 200000]}}  # Customize range based on expected value
        ))

        self.display_plot(fig, self.portfolio_value_view)

    def display_plot(self, fig, plot_view):
        """ Convert Plotly figure to HTML and display it in QWebEngineView. """
        html = fig.to_html(include_plotlyjs='cdn')
        plot_view.setHtml(html)

    def record_trade(self, action, stock, quantity, buy_price, sell_price=None):
        """ Record trade details and calculate PnL for each trade. """
        trade = {
            'action': action,
            'stock': stock,
            'quantity': quantity,
            'buy_price': buy_price,
            'sell_price': sell_price,
            'pnl': (sell_price - buy_price) * quantity if sell_price else 0,
            'is_win': sell_price > buy_price if sell_price else False
        }
        self.trades.append(trade)

    def calculate_trade_stats(self):
        """ Calculate trade statistics: Total PnL, Win/Loss Ratio, and Percentage Return. """
        total_pnl = sum(trade['pnl'] for trade in self.trades)
        wins = sum(1 for trade in self.trades if trade['is_win'])
        losses = len(self.trades) - wins

        win_loss_ratio = wins / losses if losses > 0 else wins  # Avoid division by zero
        initial_capital = 100000  # Assuming $100,000 starting capital
        percentage_return = (total_pnl / initial_capital) * 100  # Percentage of initial capital

        return total_pnl, win_loss_ratio, percentage_return, wins, losses

    def update_dashboard(self):
        """ Update the dashboard with trade statistics. """
        total_pnl, win_loss_ratio, percentage_return, wins, losses = self.calculate_trade_stats()

        # Update labels in the UI
        self.total_pnl_label.setText(f"Total PnL: ${total_pnl:,.2f}")
        self.win_loss_ratio_label.setText(f"Win/Loss Ratio: {win_loss_ratio:.2f}")
        self.percentage_return_label.setText(f"Percentage Return: {percentage_return:.2f}%")
        self.total_wins_label.setText(f"Winning Trades: {wins}")
        self.total_losses_label.setText(f"Losing Trades: {losses}")


def run_app():
    app = QApplication(sys.argv)
    window = PaperTradingSimulator()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    run_app()
