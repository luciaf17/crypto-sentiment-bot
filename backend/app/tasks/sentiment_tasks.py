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
    """Celery task to fetch and analyze BTC sentiment from multiple sources.

    Returns:
        Dictionary with per-source stats and weighted average.
    """
    symbol = "BTC"
    logger.info("Starting multi-source sentiment analysis for %s", symbol)

    try:
        analyzer = SentimentAnalyzer()
        source_data = analyzer.fetch_all_sources(symbol)

        cp_count = source_data["cryptopanic"]["count"]
        news_count = source_data["newsapi"]["count"]
        cp_avg = source_data["cryptopanic"]["avg_score"]
        news_avg = source_data["newsapi"]["avg_score"]
        fg_score = source_data["fear_greed"]["score"]
        fg_class = source_data["fear_greed"]["classification"]
        weighted_avg = source_data["weighted_avg"]

        logger.info(
            "Source stats for %s: CryptoPanic=%d items (avg=%.4f), "
            "NewsAPI=%d items (avg=%.4f), Fear&Greed=%.4f (%s)",
            symbol,
            cp_count,
            cp_avg,
            news_count,
            news_avg,
            fg_score,
            fg_class,
        )

        total_items = cp_count + news_count + 1  # +1 for Fear & Greed
        if total_items <= 1 and cp_count == 0 and news_count == 0:
            logger.warning(
                "No news items from CryptoPanic or NewsAPI for %s", symbol
            )

        # Save all scores to database
        records = analyzer.save_sentiment_scores(symbol, source_data)

        logger.info(
            "Sentiment analysis completed for %s: "
            "weighted_avg=%.4f, total_records=%d",
            symbol,
            weighted_avg,
            len(records),
        )

        return {
            "symbol": symbol,
            "weighted_avg": round(weighted_avg, 4),
            "cryptopanic": {
                "count": cp_count,
                "avg_score": round(cp_avg, 4),
            },
            "newsapi": {
                "count": news_count,
                "avg_score": round(news_avg, 4),
            },
            "fear_greed": {
                "score": round(fg_score, 4),
                "classification": fg_class,
            },
            "total_records_saved": len(records),
        }

    except Exception as e:
        logger.error("Sentiment analysis task failed for %s: %s", symbol, e)
        raise
