import os
import pandas as pd
import plotly.graph_objects as go


class CombinedGraphCreator:
    # List of stock tickers
    stock_tickers = [
        "AAPL", "MSFT", "NVDA", "ADBE", "INTC",  # Technology
        "JNJ", "PFE", "ABBV", "MRK", "TMO",  # Healthcare
        "JPM", "BAC", "WFC", "C", "GS",  # Finance
        "XOM", "CVX", "PBR", "BP", "TOT"  # Energy
    ]

    # List of sector names
    sector_names = [
        "Technology", "Healthcare", "Finance", "Energy"
    ]

    # Directory where datafetcher stores the stock and sector data
    data_dir = 'stock_data'

    @staticmethod
    def load_data(file_name):
        # Construct full file path
        filepath = os.path.join(CombinedGraphCreator.data_dir, file_name)
        absolute_filepath = os.path.abspath(filepath)
        print(f"Looking for data at {absolute_filepath}")

        if os.path.exists(filepath):
            # Load the data and parse the date column
            data = pd.read_csv(filepath, parse_dates=['Date'])
            if 'Date' in data.columns and 'Close' in data.columns:
                return data.dropna(subset=['Date', 'Close'])
            else:
                print(f"Columns 'Date' or 'Close' missing in {filepath}")
                return pd.DataFrame()
        else:
            print(f"Data not found at {filepath}")
            return pd.DataFrame()

    @staticmethod
    def plot_stock_prices():
        # Create Plotly figure for stock prices
        fig_stock = go.Figure()

        # Load and plot data for each stock
        for ticker in CombinedGraphCreator.stock_tickers:
            file_name = f'{ticker}_data.csv'
            stock_data = CombinedGraphCreator.load_data(file_name)
            if not stock_data.empty:
                print(f"Loaded data for {ticker}: {stock_data.shape[0]} rows")
                # Ensure data is sorted by date
                stock_data = stock_data.sort_values(by='Date')
                fig_stock.add_trace(go.Scatter(
                    x=stock_data['Date'], y=stock_data['Close'],
                    mode='lines', name=f"{ticker} (Stock)"
                ))
            else:
                print(f"No data to plot for {ticker}")

        # Update the layout of the stock figure
        fig_stock.update_layout(
            title='Stock Prices Over Time',
            xaxis_title='Date',
            yaxis_title='Price',
            template='plotly_white',
            legend_title='Legend'
        )

        # Show the stock figure
        fig_stock.show()

    @staticmethod
    def plot_sector_prices():
        # Create Plotly figure for sector prices
        fig_sector = go.Figure()

        # Load and plot data for each sector
        for sector in CombinedGraphCreator.sector_names:
            file_name = f'{sector}_data.csv'
            sector_data = CombinedGraphCreator.load_data(file_name)
            if not sector_data.empty:
                print(f"Loaded data for {sector}: {sector_data.shape[0]} rows")
                # Ensure data is sorted by date
                sector_data = sector_data.sort_values(by='Date')
                fig_sector.add_trace(go.Scatter(
                    x=sector_data['Date'], y=sector_data['Close'],
                    mode='lines', name=f"{sector} (Sector)"
                ))
            else:
                print(f"No data to plot for {sector}")

        # Update the layout of the sector figure
        fig_sector.update_layout(
            title='Sector Prices Over Time',
            xaxis_title='Date',
            yaxis_title='Price',
            template='plotly_white',
            legend_title='Legend'
        )

        # Show the sector figure
        fig_sector.show()


if __name__ == '__main__':
    CombinedGraphCreator.plot_stock_prices()
    CombinedGraphCreator.plot_sector_prices()
