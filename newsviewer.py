import os
import pandas as pd
from textblob import TextBlob
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QTextEdit, QHBoxLayout, QComboBox
)
from PyQt5.QtCore import Qt

# Directory where the stock data is saved
output_dir = "stock_data"

# List of stock tickers (should match what you have in the other script)
stock_tickers = [
    "AAPL", "MSFT", "NVDA", "ADBE", "INTC",  # Technology
    "JNJ", "PFE", "ABBV", "MRK", "TMO",  # Healthcare
    "JPM", "BAC", "WFC", "C", "GS",  # Finance
    "XOM", "CVX", "PBR", "BP", "TOT"  # Energy
]


class NewsSentimentAnalyzer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('News Sentiment Analyzer')
        self.setGeometry(100, 100, 800, 600)

        layout = QVBoxLayout()

        self.label = QLabel('News Sentiment Analyzer', self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 20px;")
        layout.addWidget(self.label)

        self.stock_selector = QComboBox(self)
        self.stock_selector.addItems(stock_tickers)
        self.stock_selector.currentIndexChanged.connect(self.load_and_analyze_news_data)
        layout.addWidget(self.stock_selector)

        self.news_text = QTextEdit(self)
        layout.addWidget(self.news_text)

        self.setLayout(layout)

    def load_and_analyze_news_data(self):
        selected_stock = self.stock_selector.currentText()
        news_filename = os.path.join(output_dir, f"{selected_stock}_news.csv")

        if os.path.exists(news_filename):
            self.news_data = pd.read_csv(news_filename)
            self.analyze_sentiment()
        else:
            self.news_text.setText(f"No news data found for {selected_stock}")

    def analyze_sentiment(self):
        if hasattr(self, 'news_data'):
            good_news = []
            bad_news = []

            for index, row in self.news_data.iterrows():
                title = row['title']
                analysis = TextBlob(title)
                sentiment = analysis.sentiment.polarity

                if sentiment > 0:
                    good_news.append(title)
                else:
                    bad_news.append(title)

            self.display_sentiment_result(good_news, bad_news)

    def display_sentiment_result(self, good_news, bad_news):
        self.news_text.clear()
        self.news_text.append("Good News:\n")
        for news in good_news:
            self.news_text.append(f"- {news}")

        self.news_text.append("\n\nBad News:\n")
        for news in bad_news:
            self.news_text.append(f"- {news}")


if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    ex = NewsSentimentAnalyzer()
    ex.show()
    sys.exit(app.exec_())
