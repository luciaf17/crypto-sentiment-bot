"""Signal generation service combining technical analysis and sentiment.

Produces BUY/SELL/HOLD trading signals by evaluating technical indicators
(RSI, MACD, moving averages) alongside market sentiment scores. Each signal
includes a confidence score and detailed reasoning.
"""

import logging
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models.trading import Signal, SignalAction, SentimentScore
from app.services.technical_indicators import TechnicalIndicators
from app.services.strategy_manager import StrategyManager

logger = logging.getLogger(__name__)


class SignalGenerator:
    """Generates trading signals by combining technical and sentiment analysis.

    Signal rules are determined by the active strategy configuration:
    - BUY: RSI < threshold AND sentiment > min AND price < MA(50)
    - SELL: RSI > threshold AND sentiment < 0 AND price > MA(50)
    - HOLD: any other condition

    Confidence is calculated as the proportion of conditions met (0-1).
    """

    def __init__(self) -> None:
        self.indicators = TechnicalIndicators()

    def _get_latest_sentiment(self, symbol: str) -> float | None:
        """Fetch the most recent weighted average sentiment score.

        Looks for sentiment records from the last 2 hours to ensure
        the sentiment data is reasonably fresh. Returns the average
        of all recent scores across sources.

        Args:
            symbol: Trading symbol to look up (searches for base currency,
                     e.g., "BTC" from "BTC/USDT").

        Returns:
            Average sentiment score (-1 to 1) or None if no recent data.
        """
        session = SessionLocal()
        try:
            # Extract base currency (e.g., "BTC" from "BTC/USDT")
            base_symbol = symbol.split("/")[0] if "/" in symbol else symbol

            since = datetime.now(timezone.utc) - timedelta(hours=2)

            scores = (
                session.query(SentimentScore)
                .filter(
                    SentimentScore.symbol == base_symbol,
                    SentimentScore.timestamp >= since,
                )
                .all()
            )

            if not scores:
                logger.warning(
                    "No recent sentiment data for %s (last 2 hours)", base_symbol
                )
                return None

            avg_score = sum(s.score for s in scores) / len(scores)
            return round(avg_score, 4)

        except Exception as e:
            logger.error("Failed to fetch sentiment for %s: %s", symbol, e)
            return None
        finally:
            session.close()

    def generate_signal(self, symbol: str) -> Signal | None:
        """Generate a BUY/SELL/HOLD signal for the given symbol.

        Combines technical indicators with sentiment analysis to produce
        a trading signal. The decision logic evaluates conditions based on
        the active strategy configuration.

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT").

        Returns:
            Signal ORM object (unsaved) or None if indicators unavailable.
        """
        # Get active strategy parameters
        params = StrategyManager.get_active_params()
        
        # Fetch technical indicators
        tech_data = self.indicators.get_indicators_for_symbol(symbol)
        if tech_data is None:
            logger.error("Cannot generate signal: no technical data for %s", symbol)
            return None

        current_price = tech_data["current_price"]
        rsi = tech_data["rsi"]
        macd = tech_data["macd"]
        moving_averages = tech_data["moving_averages"]
        ma_50 = moving_averages.get("ma_50")

        # Fetch sentiment score
        sentiment = self._get_latest_sentiment(symbol)

        # Build reasons dict to explain the decision
        reasons: dict[str, str | float | None] = {}
        reasons["rsi"] = rsi
        reasons["sentiment"] = sentiment
        reasons["current_price"] = current_price
        reasons["ma_50"] = ma_50
        reasons["strategy_params"] = {
            "rsi_buy": params["rsi_buy"],
            "rsi_sell": params["rsi_sell"],
            "sentiment_min": params["sentiment_min"],
        }

        # Evaluate BUY conditions using strategy params
        buy_conditions = 0
        buy_total = 3

        if rsi is not None and rsi < params["rsi_buy"]:
            buy_conditions += 1
            reasons["rsi_signal"] = "oversold"
        elif rsi is not None:
            reasons["rsi_signal"] = "neutral" if rsi <= params["rsi_sell"] else "overbought"

        if sentiment is not None and sentiment > params["sentiment_min"]:
            buy_conditions += 1
            reasons["sentiment_signal"] = "positive"
        elif sentiment is not None:
            reasons["sentiment_signal"] = "negative" if sentiment < 0 else "neutral"

        if ma_50 is not None and current_price < ma_50:
            buy_conditions += 1
            reasons["price_vs_ma50"] = "below"
        elif ma_50 is not None:
            reasons["price_vs_ma50"] = "above"

        # Evaluate SELL conditions using strategy params
        sell_conditions = 0
        sell_total = 3

        if rsi is not None and rsi > params["rsi_sell"]:
            sell_conditions += 1

        if sentiment is not None and sentiment < 0:
            sell_conditions += 1

        if ma_50 is not None and current_price > ma_50:
            sell_conditions += 1

        # Determine action: all 3 conditions must be met for BUY or SELL
        if buy_conditions == buy_total:
            action = SignalAction.BUY
            confidence = 1.0
            reasons["decision"] = f"All BUY conditions met: RSI<{params['rsi_buy']:.1f}, sentiment>{params['sentiment_min']:.2f}, price<MA(50)"
        elif sell_conditions == sell_total:
            action = SignalAction.SELL
            confidence = 1.0
            reasons["decision"] = f"All SELL conditions met: RSI>{params['rsi_sell']:.1f}, negative sentiment, price>MA(50)"
        else:
            action = SignalAction.HOLD
            # Confidence for HOLD reflects how close we are to a signal
            max_partial = max(buy_conditions, sell_conditions)
            confidence = round(1.0 - (max_partial / 3.0), 2)
            reasons["decision"] = (
                f"HOLD: buy_conditions={buy_conditions}/3, "
                f"sell_conditions={sell_conditions}/3"
            )

        # Add MACD context to reasons (informational)
        if macd is not None:
            reasons["macd_line"] = macd["macd_line"]
            reasons["macd_signal"] = macd["signal_line"]
            reasons["macd_histogram"] = macd["histogram"]
            if macd["histogram"] > 0:
                reasons["macd_trend"] = "bullish"
            else:
                reasons["macd_trend"] = "bearish"

        # Build the Signal object
        signal = Signal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            price_at_signal=current_price,
            reasons=reasons,
            technical_indicators={
                "rsi": rsi,
                "macd": macd,
                "moving_averages": moving_averages,
                "data_points": tech_data["data_points"],
            },
            sentiment_score=sentiment,
            timestamp=datetime.now(timezone.utc),
        )

        logger.info(
            "Generated signal for %s: action=%s, confidence=%.2f, price=%.2f (using strategy params)",
            symbol,
            action.value,
            confidence,
            current_price,
        )

        return signal

    def save_signal(self, signal: Signal) -> Signal:
        """Persist a Signal record to the database.

        Args:
            signal: Signal ORM object to save.

        Returns:
            The saved Signal object with its assigned id.
        """
        session = SessionLocal()
        try:
            session.add(signal)
            session.commit()
            session.refresh(signal)
            logger.info(
                "Saved signal id=%d for %s: %s (confidence=%.2f)",
                signal.id,
                signal.symbol,
                signal.action.value,
                signal.confidence,
            )
            return signal
        except Exception as e:
            session.rollback()
            logger.error("Failed to save signal: %s", e)
            raise
        finally:
            session.close()