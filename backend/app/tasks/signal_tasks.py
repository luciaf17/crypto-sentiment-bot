"""Celery tasks for periodic trading signal generation."""

import logging

from app.services.signal_generator import SignalGenerator
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.signal_tasks.generate_trading_signal",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def generate_trading_signal(self) -> dict:
    """Generate a trading signal for BTC/USDT.

    Runs every hour via Celery beat. Combines technical indicators
    (RSI, MACD, moving averages) with sentiment analysis to produce
    a BUY/SELL/HOLD signal with confidence score.

    Retry logic: exponential backoff starting at ~4s, capped at 600s,
    up to 3 retries for any exception.

    Returns:
        Dictionary with signal details for Celery result backend.
    """
    symbol = "BTC/USDT"
    logger.info("Starting signal generation for %s", symbol)

    try:
        generator = SignalGenerator()
        signal = generator.generate_signal(symbol)

        if signal is None:
            logger.warning(
                "Signal generation returned None for %s — "
                "likely insufficient price data",
                symbol,
            )
            return {
                "symbol": symbol,
                "status": "skipped",
                "reason": "Insufficient data for signal generation",
            }

        # Persist the signal to the database
        saved_signal = generator.save_signal(signal)

        logger.info(
            "Signal generated for %s: action=%s, confidence=%.2f, "
            "rsi=%s, sentiment=%s, price=%.2f",
            symbol,
            saved_signal.action.value,
            saved_signal.confidence,
            saved_signal.reasons.get("rsi"),
            saved_signal.sentiment_score,
            saved_signal.price_at_signal,
        )

        return {
            "symbol": symbol,
            "status": "generated",
            "signal_id": saved_signal.id,
            "action": saved_signal.action.value,
            "confidence": round(saved_signal.confidence, 2),
            "price_at_signal": saved_signal.price_at_signal,
            "sentiment_score": saved_signal.sentiment_score,
            "rsi": saved_signal.reasons.get("rsi"),
            "decision": saved_signal.reasons.get("decision"),
        }

    except Exception as e:
        logger.error("Signal generation task failed for %s: %s", symbol, e)
        raise
