import logging
from datetime import datetime, timezone

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from app.database import SessionLocal
from app.models.trading import SentimentScore

from .cryptopanic_scraper import CryptoPanicScraper
from .fear_greed_index import FearGreedIndex
from .newsapi_scraper import NewsAPIScraper

logger = logging.getLogger(__name__)

# Source weights for composite score
WEIGHT_CRYPTOPANIC = 0.40
WEIGHT_NEWSAPI = 0.40
WEIGHT_FEAR_GREED = 0.20


class SentimentAnalyzer:
    """Multi-source sentiment analyzer for cryptocurrencies."""

    def __init__(self) -> None:
        self.cryptopanic = CryptoPanicScraper()
        self.newsapi = NewsAPIScraper()
        self.fear_greed = FearGreedIndex()
        self.vader = SentimentIntensityAnalyzer()

    def analyze_text(self, text: str) -> float:
        """Analyze the sentiment of a text string using VADER.

        Returns:
            Compound sentiment score between -1 and 1.
        """
        scores = self.vader.polarity_scores(text)
        return scores["compound"]

    def fetch_all_sources(self, symbol: str) -> dict:
        """Fetch sentiment data from all sources for a symbol.

        Args:
            symbol: Cryptocurrency symbol (e.g. "BTC").

        Returns:
            Dict with per-source scores, items, and weighted average.
        """
        result: dict = {
            "symbol": symbol,
            "cryptopanic": {"items": [], "avg_score": 0.0, "count": 0},
            "newsapi": {"items": [], "avg_score": 0.0, "count": 0},
            "fear_greed": {"score": 0.0, "value": 50, "classification": "Neutral"},
            "weighted_avg": 0.0,
        }

        # --- CryptoPanic ---
        cp_posts = self.cryptopanic.get_news(currencies=symbol)
        cp_scores: list[float] = []
        for post in cp_posts:
            vader_score = self.analyze_text(post["title"])
            # Blend VADER text score with vote-based sentiment
            vote_score = post.get("sentiment_score", 0.0)
            combined = (vader_score + vote_score) / 2.0
            cp_scores.append(combined)
            result["cryptopanic"]["items"].append(
                {
                    "text": post["title"],
                    "score": combined,
                    "source_name": post.get("source_name", ""),
                    "published_at": post.get("published_at", ""),
                    "url": post.get("url", ""),
                }
            )
        if cp_scores:
            result["cryptopanic"]["avg_score"] = sum(cp_scores) / len(cp_scores)
            result["cryptopanic"]["count"] = len(cp_scores)

        # --- NewsAPI ---
        query = f"{symbol} cryptocurrency"
        articles = self.newsapi.get_crypto_news(query=query)
        news_scores: list[float] = []
        for article in articles:
            text = f"{article['title']} {article.get('description', '') or ''}"
            score = self.analyze_text(text)
            news_scores.append(score)
            result["newsapi"]["items"].append(
                {
                    "text": article["title"],
                    "description": article.get("description", ""),
                    "score": score,
                    "source": article.get("source", ""),
                    "published_at": article.get("published_at", ""),
                    "url": article.get("url", ""),
                }
            )
        if news_scores:
            result["newsapi"]["avg_score"] = sum(news_scores) / len(news_scores)
            result["newsapi"]["count"] = len(news_scores)

        # --- Fear & Greed Index ---
        fg = self.fear_greed.get_current()
        result["fear_greed"] = {
            "score": fg["normalized_score"],
            "value": fg["value"],
            "classification": fg["classification"],
        }

        # --- Weighted average ---
        cp_avg = result["cryptopanic"]["avg_score"]
        news_avg = result["newsapi"]["avg_score"]
        fg_score = result["fear_greed"]["score"]

        # Only include sources that returned data in the weighting
        total_weight = 0.0
        weighted_sum = 0.0

        if result["cryptopanic"]["count"] > 0:
            weighted_sum += WEIGHT_CRYPTOPANIC * cp_avg
            total_weight += WEIGHT_CRYPTOPANIC

        if result["newsapi"]["count"] > 0:
            weighted_sum += WEIGHT_NEWSAPI * news_avg
            total_weight += WEIGHT_NEWSAPI

        # Fear & Greed always contributes (free API, no key needed)
        weighted_sum += WEIGHT_FEAR_GREED * fg_score
        total_weight += WEIGHT_FEAR_GREED

        if total_weight > 0:
            result["weighted_avg"] = weighted_sum / total_weight

        logger.info(
            "Multi-source sentiment for %s: "
            "CryptoPanic=%.4f (%d items), NewsAPI=%.4f (%d items), "
            "Fear&Greed=%.4f (%s), weighted_avg=%.4f",
            symbol,
            cp_avg,
            result["cryptopanic"]["count"],
            news_avg,
            result["newsapi"]["count"],
            fg_score,
            fg["classification"],
            result["weighted_avg"],
        )

        return result

    def save_sentiment_scores(
        self, symbol: str, source_data: dict
    ) -> list[SentimentScore]:
        """Save individual sentiment scores from all sources to the database.

        Args:
            symbol: Cryptocurrency symbol.
            source_data: Result from fetch_all_sources().

        Returns:
            List of saved SentimentScore records.
        """
        session = SessionLocal()
        records: list[SentimentScore] = []
        now = datetime.now(timezone.utc)

        try:
            # Save CryptoPanic items
            for item in source_data["cryptopanic"]["items"]:
                record = SentimentScore(
                    symbol=symbol,
                    score=item["score"],
                    source="cryptopanic",
                    raw_text=item["text"][:500],
                    timestamp=now,
                )
                session.add(record)
                records.append(record)

            # Save NewsAPI items
            for item in source_data["newsapi"]["items"]:
                record = SentimentScore(
                    symbol=symbol,
                    score=item["score"],
                    source="newsapi",
                    raw_text=item["text"][:500],
                    timestamp=now,
                )
                session.add(record)
                records.append(record)

            # Save Fear & Greed as a single record
            fg = source_data["fear_greed"]
            record = SentimentScore(
                symbol=symbol,
                score=fg["score"],
                source="fear_greed",
                raw_text=f"Fear & Greed Index: {fg['value']} ({fg['classification']})",
                timestamp=now,
            )
            session.add(record)
            records.append(record)

            session.commit()
            for r in records:
                session.refresh(r)

            logger.info(
                "Saved %d sentiment scores for %s "
                "(cryptopanic=%d, newsapi=%d, fear_greed=1)",
                len(records),
                symbol,
                source_data["cryptopanic"]["count"],
                source_data["newsapi"]["count"],
            )
            return records

        except Exception as e:
            session.rollback()
            logger.error("Error saving sentiment scores: %s", e)
            raise
        finally:
            session.close()
