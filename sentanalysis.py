import os
import pandas as pd
from textblob import TextBlob
import plotly.graph_objects as go

# Directory where the news data is stored
news_dir = "stock_data"

# List of stock tickers
stock_tickers = [
    "AAPL", "MSFT", "NVDA", "ADBE", "INTC",  # Technology
    "JNJ", "PFE", "ABBV", "MRK", "TMO",  # Healthcare
    "JPM", "BAC", "WFC", "C", "GS",  # Finance
    "XOM", "CVX", "PBR", "BP", "TOT"  # Energy
]


class SentimentAnalysis:
    @staticmethod
    def analyze_sentiment(news_file):
        news_df = pd.read_csv(news_file)

        if 'headline' not in news_df.columns:
            print(f"Column 'headline' not found in {news_file}")
            return 0

        sentiment_scores = []

        for headline in news_df['headline']:
            analysis = TextBlob(headline)
            sentiment_scores.append(analysis.sentiment.polarity)

        if not sentiment_scores:
            return 0

        average_score = sum(sentiment_scores) / len(sentiment_scores)
        normalized_score = (average_score + 1) / 2  # Normalize to 0-1
        return max(0, min(1, normalized_score))

    @staticmethod
    def get_sentiment_scores():
        sentiment_scores = {}

        for ticker in stock_tickers:
            news_file = os.path.join(news_dir, f"{ticker}_news.csv")

            if os.path.exists(news_file):
                sentiment_score = SentimentAnalysis.analyze_sentiment(news_file)
            else:
                sentiment_score = 0  # No news available, default to 0 sentiment

            sentiment_scores[ticker] = sentiment_score

        return sentiment_scores

    @staticmethod
    def plot_sentiments():
        sentiment_scores = SentimentAnalysis.get_sentiment_scores()
        symbols = list(sentiment_scores.keys())
        scores = list(sentiment_scores.values())

        fig = go.Figure(data=[
            go.Bar(
                x=symbols,
                y=scores,
                text=scores,
                textposition='auto',
                marker_color='lightskyblue'
            )
        ])

        fig.update_layout(
            title="Stock Sentiment Scores",
            xaxis_title="Stock Symbol",
            yaxis_title="Sentiment Score (0-1)",
            template='plotly_dark'
        )

        fig.show()


if __name__ == "__main__":
    SentimentAnalysis.plot_sentiments()
