import logging
import time
from datetime import datetime, timedelta, timezone

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.database import SessionLocal
from app.models.trading import SentimentScore

from .twitter_scraper import TwitterScraper

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Analyzes sentiment of cryptocurrency-related tweets."""

    def __init__(self) -> None:
        self.scraper = TwitterScraper()
        self.vader = SentimentIntensityAnalyzer()

    def fetch_tweets(self, query: str, limit: int = 20) -> list[dict]:
        """Fetch recent tweets for a query with rate-limit handling.

        Args:
            query: Search query string.
            limit: Maximum number of tweets to fetch.

        Returns:
            List of tweet dicts from TwitterScraper.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                since_date = datetime.now(timezone.utc) - timedelta(hours=24)
                return self.scraper.search_tweets(
                    query=query, limit=limit, since_date=since_date
                )
            except Exception as e:
                wait = 2 ** (attempt + 1)
                logger.warning(
                    "Rate limit or error fetching tweets (attempt %d/%d): %s. "
                    "Retrying in %ds...",
                    attempt + 1,
                    max_retries,
                    e,
                    wait,
                )
                time.sleep(wait)

        logger.error("Failed to fetch tweets after %d attempts", max_retries)
        return []

    def analyze_sentiment(self, text: str) -> float:
        """Analyze the sentiment of a text string using VADER.

        Args:
            text: The text to analyze.

        Returns:
            Compound sentiment score between -1 (negative) and 1 (positive).
        """
        scores = self.vader.polarity_scores(text)
        return scores["compound"]

    def process_tweets(self, symbol: str) -> float:
        """Fetch tweets about a symbol, analyze sentiment, and return average.

        Args:
            symbol: Cryptocurrency symbol (e.g. 'BTC').

        Returns:
            Average sentiment score, or 0.0 if no tweets found.
        """
        query = f"${symbol} OR #{symbol} crypto"
        logger.info("Processing tweets for symbol %s", symbol)

        tweets = self.fetch_tweets(query)
        if not tweets:
            logger.warning("No tweets found for %s", symbol)
            return 0.0

        scores: list[float] = []
        for tweet in tweets:
            score = self.analyze_sentiment(tweet["text"])
            scores.append(score)

        avg_score = sum(scores) / len(scores)
        logger.info(
            "Sentiment for %s: avg=%.4f from %d tweets",
            symbol,
            avg_score,
            len(scores),
        )
        return avg_score

    def save_sentiment_scores(
        self, symbol: str, tweets: list[dict], scores: list[float]
    ) -> list[SentimentScore]:
        """Save individual sentiment scores to the database.

        Args:
            symbol: Cryptocurrency symbol.
            tweets: List of tweet dicts.
            scores: Corresponding sentiment scores.

        Returns:
            List of saved SentimentScore records.
        """
        session = SessionLocal()
        records: list[SentimentScore] = []
        try:
            for tweet, score in zip(tweets, scores):
                record = SentimentScore(
                    symbol=symbol,
                    score=score,
                    source="twitter",
                    raw_text=tweet["text"][:500],
                    timestamp=tweet["created_at"],
                )
                session.add(record)
                records.append(record)

            session.commit()
            for r in records:
                session.refresh(r)

            logger.info(
                "Saved %d sentiment scores for %s", len(records), symbol
            )
            return records

        except Exception as e:
            session.rollback()
            logger.error("Error saving sentiment scores: %s", e)
            raise
        finally:
            session.close()
