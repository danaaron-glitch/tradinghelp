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

# Sector ETFs and actual sector names
sector_etfs = {
    "Technology": "XLK",
    "Healthcare": "XLV",
    "Finance": "XLF",
    "Energy": "XLE"
}


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
    def get_sentiment_scores(entities, label_type):
        sentiment_scores = {}

        for entity in entities:
            news_file = os.path.join(news_dir, f"{label_type}_{entity}_news.csv")

            if os.path.exists(news_file):
                sentiment_score = SentimentAnalysis.analyze_sentiment(news_file)
            else:
                sentiment_score = 0  # No news available, default to 0 sentiment

            # Round sentiment scores to 3 decimal places
            sentiment_scores[entity] = round(sentiment_score, 3)

        return sentiment_scores

    @staticmethod
    def plot_sentiments(sentiment_scores, title, symbols_label='Stock Symbol', replace_names=None):
        # Sort the scores in descending order
        sorted_scores = dict(sorted(sentiment_scores.items(), key=lambda item: item[1], reverse=True))

        symbols = list(sorted_scores.keys())
        scores = list(sorted_scores.values())

        # Replace names if provided
        if replace_names:
            symbols = [replace_names.get(symbol, symbol) for symbol in symbols]

        # Create a continuous color scale from orange to green
        color_scale = [
            [0, 'rgb(255, 165, 0)'],  # Orange
            [0.5, 'rgb(255, 218, 83)'],  # Yellow
            [0.75, 'rgb(173, 255, 47)'],  # GreenYellow
            [1, 'rgb(50, 205, 50)']  # Green
        ]

        fig = go.Figure(data=[
            go.Bar(
                x=symbols,
                y=scores,
                text=[f'{score:.3f}' for score in scores],
                textposition='auto',
                marker=dict(color=scores, colorscale=color_scale, showscale=True)
            )
        ])

        fig.update_layout(
            title=title,
            xaxis_title=symbols_label,
            yaxis_title="Sentiment Score (0-1)",
            yaxis=dict(
                tickvals=[0, 0.5, 1],
                ticktext=['0 (Worst Score)', '0.5', '1 (Best Score)'],
                range=[0, 1],
                showgrid=True  # Add grid lines to the Y-axis
            ),
            xaxis=dict(
                showgrid=True  # Add grid lines to the X-axis
            ),
            template='plotly_white',
            font=dict(
                family="Arial, sans-serif",
                size=14,
                color="Black"
            ),
            plot_bgcolor='rgba(0, 0, 0, 0)',
            paper_bgcolor='rgba(0, 0, 0, 0)',
            annotations=[
                {
                    'x': symbols[0],
                    'y': 1.05,
                    'xref': 'x',
                    'yref': 'paper',
                    'text': 'Buy',
                    'showarrow': False,
                    'font': {
                        'size': 16,
                        'color': 'green'
                    }
                },
                {
                    'x': symbols[-1],
                    'y': 1.05,
                    'xref': 'x',
                    'yref': 'paper',
                    'text': 'Sell',
                    'showarrow': False,
                    'font': {
                        'size': 16,
                        'color': 'red'
                    }
                }
            ]
        )

        return fig


if __name__ == "__main__":
    # Plot sentiment scores for individual stocks
    stock_sentiment_scores = SentimentAnalysis.get_sentiment_scores(stock_tickers, "stock")
    stock_fig = SentimentAnalysis.plot_sentiments(stock_sentiment_scores, "Stock Sentiment Scores")
    stock_fig.show()

    # Plot sentiment scores for sectors
    sector_sentiment_scores = SentimentAnalysis.get_sentiment_scores([etf for etf in sector_etfs.values()], "sector")
    # Replace ETF symbols with actual sector names for better readability
    sector_fig = SentimentAnalysis.plot_sentiments(sector_sentiment_scores, "Sector Sentiment Scores",
                                                   symbols_label='Sector',
                                                   replace_names={etf: sector for sector, etf in sector_etfs.items()})
    sector_fig.show()
