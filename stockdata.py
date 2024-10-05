import os
import json
import time
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from eventregistry import EventRegistry, QueryArticlesIter

# Define the stock tickers for individual stocks and sectors
individual_stocks = [
    "AAPL", "MSFT", "NVDA", "ADBE", "INTC",  # Technology
    "JNJ", "PFE", "ABBV", "MRK", "TMO",  # Healthcare
    "JPM", "BAC", "WFC", "C", "GS",  # Finance
    "XOM", "CVX", "PBR", "BP", "TOT"  # Energy (replacing Consumer Discretionary)
]

# Define the sector ETFs for broader sector data
sector_etfs = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Finance": "XLF",
    "Energy": "XLE"
}

# Define the period (past 11 years)
end_date = datetime.today().strftime('%Y-%m-%d')
start_date = (datetime.today() - timedelta(days=11 * 365)).strftime('%Y-%m-%d')

# Directory to save CSV files
output_dir = "stock_data"
os.makedirs(output_dir, exist_ok=True)

# Define the Event Registry API key
api_key = 'b47b43f2-af8e-4d6e-a413-1b4d45524341'  # Replace with your actual API key

# File to store timestamp information
timestamp_file = os.path.join(output_dir, "timestamps.json")
time_limit = 24 * 60 * 60  # 24 hours in seconds

# Initialize the EventRegistry
er = EventRegistry(apiKey=api_key)


# Function to fetch and save individual stock data
def fetch_and_save_individual_data():
    for ticker in individual_stocks:
        stock_data = yf.download(ticker, start=start_date, end=end_date)
        stock_data['Ticker'] = ticker
        individual_filename = os.path.join(output_dir, f"{ticker}_data.csv")
        stock_data.to_csv(individual_filename)
        print(f"Data for {ticker} saved to {individual_filename}")
        fetch_and_save_news(ticker)


# Function to fetch and save sector data
def fetch_and_save_sector_data():
    for sector, etf in sector_etfs.items():
        sector_data = yf.download(etf, start=start_date, end=end_date)
        sector_data['ETF'] = etf
        sector_filename = os.path.join(output_dir, f"{sector}_data.csv")
        sector_data.to_csv(sector_filename)
        print(f"Data for {sector} sector saved to {sector_filename}")


# Function to fetch and save news data for a given ticker
def fetch_and_save_news(ticker):
    if not is_valid_time_to_fetch(ticker):
        print(f"Using cached news data for {ticker}")
        return

    try:
        q = QueryArticlesIter(
            keywords=ticker,
            dataType="news",
            isDuplicateFilter="skipDuplicates"
        )

        headlines = []
        for article in q.execQuery(er, maxItems=100):
            if article['lang'] == "eng":
                headlines.append(article['title'])

        save_headlines(ticker, headlines)
        update_timestamp(ticker)
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")


# Function to save headlines
def save_headlines(stock_symbol, headlines):
    if headlines:
        news_filename = os.path.join(output_dir, f"{stock_symbol}_news.csv")
        news_df = pd.DataFrame(headlines, columns=['headline'])
        news_df.to_csv(news_filename, index=False)
        print(f"News for {stock_symbol} saved to {news_filename}")
    else:
        print(f"No headlines to save for {stock_symbol}")


# Helper function to update timestamp
def update_timestamp(stock_symbol):
    if os.path.exists(timestamp_file):
        with open(timestamp_file, 'r') as file:
            timestamps = json.load(file)
    else:
        timestamps = {}

    timestamps[stock_symbol] = time.time()
    with open(timestamp_file, 'w') as file:
        json.dump(timestamps, file)


# Helper function to check if it's valid time to fetch
def is_valid_time_to_fetch(stock_symbol):
    if os.path.exists(timestamp_file):
        with open(timestamp_file, 'r') as file:
            timestamps = json.load(file)

        if stock_symbol in timestamps:
            last_fetch_time = timestamps[stock_symbol]
            if time.time() - last_fetch_time < time_limit:
                return False
    return True


if __name__ == "__main__":
    fetch_and_save_individual_data()
    fetch_and_save_sector_data()
