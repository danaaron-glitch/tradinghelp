import os
import json
import time
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf
from eventregistry import EventRegistry, QueryArticlesIter

# Define the stock tickers for individual stocks
individual_stocks = [
    "AAPL", "MSFT", "NVDA", "ADBE", "INTC",  # Technology
    "JNJ", "PFE", "ABBV", "MRK", "TMO",  # Healthcare
    "JPM", "CME", "WFC", "CPAY", "GS",  # Finance (Updated)
    "XOM", "CVX", "PBR", "BP", "PSX"  # Energy (Updated)
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

# Directories to save CSV files
stock_data_dir = "Stock Data"
sector_data_dir = "Sector Data"
stock_news_data_dir = "Stock News Data"

# Create directories if they don't exist
os.makedirs(stock_data_dir, exist_ok=True)
os.makedirs(sector_data_dir, exist_ok=True)
os.makedirs(stock_news_data_dir, exist_ok=True)

# Define the Event Registry API key
api_key = 'b47b43f2-af8e-4d6e-a413-1b4d45524341'  # Replace with your actual API key

# File to store timestamp information
timestamp_file = os.path.join(stock_news_data_dir, "timestamps.json")
time_limit = 24 * 60 * 60  # 24 hours in seconds

# Initialize the EventRegistry
er = EventRegistry(apiKey=api_key)

data_summary = {
    "stock_data": 0,
    "stock_news": 0,
    "sector_data": 0,
    "sector_news": 0,
    "total_stocks": len(individual_stocks),
    "total_sectors": len(sector_etfs)
}


def log_status(progress, total, label, ticker_type=""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if ticker_type:
        print(f"{now} - {progress}/{total} {label} retrieved for {ticker_type}")
    else:
        print(f"{now} - {progress}/{total} {label} retrieved")


# Function to fetch and save individual stock data
def fetch_and_save_individual_data():
    stock_progress = 0
    news_progress = 0

    for ticker in individual_stocks:
        try:
            stock_data = yf.download(ticker, start=start_date, end=end_date)
            stock_data['Ticker'] = ticker
            individual_filename = os.path.join(stock_data_dir, f"{ticker}_data.csv")
            stock_data.to_csv(individual_filename)
            stock_progress += 1
            data_summary["stock_data"] += 1
            log_status(stock_progress, len(individual_stocks), "stock data", ticker)

            fetch_and_save_news(ticker, "stock")
            news_progress += 1
            data_summary["stock_news"] += 1
            log_status(news_progress, len(individual_stocks), "stock news", ticker)
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")


# Function to fetch and save sector data
def fetch_and_save_sector_data():
    sector_progress = 0
    news_progress = 0

    for sector, etf in sector_etfs.items():
        try:
            sector_data = yf.download(etf, start=start_date, end=end_date)
            sector_data['ETF'] = etf
            sector_filename = os.path.join(sector_data_dir, f"{sector}_data.csv")
            sector_data.to_csv(sector_filename)
            sector_progress += 1
            data_summary["sector_data"] += 1
            log_status(sector_progress, len(sector_etfs), "sector data", sector)

            fetch_and_save_news(etf, "sector")
            news_progress += 1
            data_summary["sector_news"] += 1
            log_status(news_progress, len(sector_etfs), "sector news", sector)
        except Exception as e:
            print(f"Error fetching data for {sector}: {e}")


# Function to fetch and save news data for a given ticker or sector ETF
def fetch_and_save_news(label, label_type):
    if not is_valid_time_to_fetch(label):
        try:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{now} - Using cached news data for {label}")
            return
        except Exception as e:
            print(f"Error using cached news for {label}: {e}")

    try:
        q = QueryArticlesIter(
            keywords=label,
            dataType="news",
            isDuplicateFilter="skipDuplicates"
        )

        headlines = []
        for article in q.execQuery(er, maxItems=100):
            if article['lang'] == "eng":
                headlines.append(article['title'])

        save_headlines(label, headlines, label_type)
        update_timestamp(label)
    except Exception as e:
        print(f"Error fetching news for {label}: {e}")


# Function to save headlines
def save_headlines(label, headlines, label_type):
    if headlines:
        news_filename = os.path.join(stock_news_data_dir, f"{label_type}_{label}_news.csv")
        news_df = pd.DataFrame(headlines, columns=['headline'])
        news_df.to_csv(news_filename, index=False)
        print(f"News for {label} saved to {news_filename}")
    else:
        print(f"No headlines to save for {label}")


# Helper function to update timestamp
def update_timestamp(label):
    if os.path.exists(timestamp_file):
        with open(timestamp_file, 'r') as file:
            timestamps = json.load(file)
    else:
        timestamps = {}

    timestamps[label] = time.time()
    with open(timestamp_file, 'w') as file:
        json.dump(timestamps, file)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{now} - Timestamp updated for {label}")


# Helper function to check if it's valid time to fetch
def is_valid_time_to_fetch(label):
    if os.path.exists(timestamp_file):
        with open(timestamp_file, 'r') as file:
            timestamps = json.load(file)

        if label in timestamps:
            last_fetch_time = timestamps[label]
            if time.time() - last_fetch_time < time_limit:
                return False
    return True


# Function to print summary
def print_summary():
    print("\nSummary of Data Retrieval:")
    print(f"Stock Data Retrieved: {data_summary['stock_data']}/{data_summary['total_stocks']}")
    print(f"Stock News Retrieved: {data_summary['stock_news']}/{data_summary['total_stocks']}")
    print(f"Sector Data Retrieved: {data_summary['sector_data']}/{data_summary['total_sectors']}")
    print(f"Sector News Retrieved: {data_summary['sector_news']}/{data_summary['total_sectors']}")

    if data_summary['stock_data'] == data_summary['total_stocks'] and \
            data_summary['stock_news'] == data_summary['total_stocks'] and \
            data_summary['sector_data'] == data_summary['total_sectors'] and \
            data_summary['sector_news'] == data_summary['total_sectors']:
        print("All data retrieved successfully.")
    else:
        missing_parts = []
        if data_summary['stock_data'] < data_summary['total_stocks']:
            missing_parts.append("stock data")
        if data_summary['stock_news'] < data_summary['total_stocks']:
            missing_parts.append("stock news")
        if data_summary['sector_data'] < data_summary['total_sectors']:
            missing_parts.append("sector data")
        if data_summary['sector_news'] < data_summary['total_sectors']:
            missing_parts.append("sector news")
        print(f"Missing: {', '.join(missing_parts)}")


if __name__ == "__main__":
    fetch_and_save_individual_data()
    fetch_and_save_sector_data()
    print_summary()
