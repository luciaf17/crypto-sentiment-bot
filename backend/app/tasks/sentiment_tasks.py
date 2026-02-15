import logging

from app.services.sentiment_analyzer import SentimentAnalyzer
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.sentiment_tasks.analyze_btc_sentiment",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def analyze_btc_sentiment(self) -> dict:
    """Celery task to fetch and analyze BTC tweet sentiment.

    Returns:
        Dictionary with symbol, average score, and count of tweets analyzed.
    """
    symbol = "BTC"
    logger.info("Starting sentiment analysis task for %s", symbol)

    try:
        analyzer = SentimentAnalyzer()

        query = f"${symbol} OR #{symbol} crypto"
        tweets = analyzer.fetch_tweets(query)

        if not tweets:
            logger.warning("No tweets found for %s, skipping", symbol)
            return {"symbol": symbol, "avg_score": 0.0, "tweet_count": 0}

        scores = [analyzer.analyze_sentiment(t["text"]) for t in tweets]
        avg_score = sum(scores) / len(scores)

        analyzer.save_sentiment_scores(symbol, tweets, scores)

        logger.info(
            "Sentiment analysis completed for %s: avg=%.4f, tweets=%d",
            symbol,
            avg_score,
            len(tweets),
        )
        return {
            "symbol": symbol,
            "avg_score": round(avg_score, 4),
            "tweet_count": len(tweets),
        }

    except Exception as e:
        logger.error("Sentiment analysis task failed for %s: %s", symbol, e)
        raise
