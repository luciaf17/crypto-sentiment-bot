"""Technical indicators for crypto trading signals.

Provides RSI, MACD, and Moving Average calculations using pandas.
All indicators follow standard financial formulas used in technical analysis.
"""

import logging

import pandas as pd
from sqlalchemy import desc

from app.database import SessionLocal
from app.models.trading import PriceHistory

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Calculates technical indicators from price data.

    Uses pandas for efficient vectorized calculations of RSI, MACD,
    and moving averages. Can fetch price data directly from the database
    for a given symbol.
    """

    # Minimum data points required for each indicator
    MIN_RSI_PERIODS = 15      # At least period + 1 data points
    MIN_MACD_PERIODS = 35     # MACD needs 26-period EMA + some buffer
    MIN_MA_PERIODS = 200      # MA(200) needs at least 200 data points

    def calculate_rsi(self, prices: list[float], period: int = 14) -> float | None:
        """Calculate the Relative Strength Index (RSI).

        RSI measures momentum on a 0-100 scale:
        - Below 30: oversold (potential buy)
        - Above 70: overbought (potential sell)
        - 50: neutral

        Uses the Wilder smoothing method (exponential moving average)
        which is the standard RSI calculation.

        Args:
            prices: List of closing prices (oldest first).
            period: Lookback period for RSI calculation (default 14).

        Returns:
            RSI value (0-100) or None if insufficient data.
        """
        if len(prices) < period + 1:
            logger.warning(
                "Insufficient data for RSI: need %d prices, got %d",
                period + 1,
                len(prices),
            )
            return None

        series = pd.Series(prices)
        delta = series.diff()

        # Separate gains (positive deltas) and losses (negative deltas)
        gains = delta.where(delta > 0, 0.0)
        losses = (-delta).where(delta < 0, 0.0)

        # Wilder smoothing: use exponential moving average with alpha = 1/period
        avg_gain = gains.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = losses.ewm(alpha=1 / period, min_periods=period).mean()

        # Avoid division by zero: if avg_loss is 0, RSI is 100
        last_avg_loss = avg_loss.iloc[-1]
        if last_avg_loss == 0:
            return 100.0

        rs = avg_gain.iloc[-1] / last_avg_loss
        rsi = 100.0 - (100.0 / (1.0 + rs))

        return round(rsi, 2)

    def calculate_macd(
        self, prices: list[float]
    ) -> dict[str, float | None] | None:
        """Calculate the Moving Average Convergence Divergence (MACD).

        MACD uses three components:
        - MACD line: difference between 12-period and 26-period EMA
        - Signal line: 9-period EMA of the MACD line
        - Histogram: MACD line minus signal line

        Trading interpretation:
        - MACD crosses above signal: bullish
        - MACD crosses below signal: bearish
        - Histogram growing: strengthening trend

        Args:
            prices: List of closing prices (oldest first).

        Returns:
            Dict with 'macd_line', 'signal_line', 'histogram' or None
            if insufficient data.
        """
        if len(prices) < self.MIN_MACD_PERIODS:
            logger.warning(
                "Insufficient data for MACD: need %d prices, got %d",
                self.MIN_MACD_PERIODS,
                len(prices),
            )
            return None

        series = pd.Series(prices)

        # Standard MACD parameters: 12-period fast, 26-period slow, 9-period signal
        ema_12 = series.ewm(span=12, adjust=False).mean()
        ema_26 = series.ewm(span=26, adjust=False).mean()

        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            "macd_line": round(macd_line.iloc[-1], 4),
            "signal_line": round(signal_line.iloc[-1], 4),
            "histogram": round(histogram.iloc[-1], 4),
        }

    def calculate_moving_averages(
        self, prices: list[float]
    ) -> dict[str, float | None]:
        """Calculate Simple Moving Averages for key periods.

        Moving averages smooth out price data to identify trends:
        - MA(20): short-term trend (approx 1 month of daily data)
        - MA(50): medium-term trend (approx 2.5 months)
        - MA(200): long-term trend (approx 10 months)

        Price above MA = bullish, price below MA = bearish.
        MA crossovers (e.g., golden cross: MA50 crosses above MA200) are
        also important signals.

        Args:
            prices: List of closing prices (oldest first).

        Returns:
            Dict with 'ma_20', 'ma_50', 'ma_200' (None if not enough data).
        """
        series = pd.Series(prices)
        result: dict[str, float | None] = {}

        for period, key in [(20, "ma_20"), (50, "ma_50"), (200, "ma_200")]:
            if len(prices) >= period:
                ma = series.rolling(window=period).mean()
                result[key] = round(ma.iloc[-1], 4)
            else:
                logger.warning(
                    "Insufficient data for MA(%d): need %d prices, got %d",
                    period,
                    period,
                    len(prices),
                )
                result[key] = None

        return result

    def get_indicators_for_symbol(self, symbol: str) -> dict | None:
        """Fetch recent prices from database and calculate all indicators.

        Retrieves the most recent price records for the given symbol and
        calculates RSI, MACD, and moving averages. Since prices are stored
        every 5 minutes, we fetch enough records to cover MA(200).

        Args:
            symbol: Trading pair symbol (e.g., "BTC/USDT").

        Returns:
            Dict with all indicators, current price, and metadata,
            or None if no price data is available.
        """
        session = SessionLocal()
        try:
            # Fetch enough data points for the longest indicator (MA 200)
            # plus a buffer for MACD/RSI warm-up
            rows = (
                session.query(PriceHistory)
                .filter(PriceHistory.symbol == symbol)
                .order_by(desc(PriceHistory.timestamp))
                .limit(250)
                .all()
            )

            if not rows:
                logger.warning("No price data found for symbol %s", symbol)
                return None

            # Reverse to chronological order (oldest first) for calculations
            rows.reverse()
            prices = [row.close for row in rows]
            current_price = prices[-1]

            rsi = self.calculate_rsi(prices)
            macd = self.calculate_macd(prices)
            moving_averages = self.calculate_moving_averages(prices)

            return {
                "symbol": symbol,
                "current_price": current_price,
                "data_points": len(prices),
                "rsi": rsi,
                "macd": macd,
                "moving_averages": moving_averages,
                "latest_timestamp": rows[-1].timestamp.isoformat(),
            }

        except Exception as e:
            logger.error(
                "Failed to calculate indicators for %s: %s", symbol, e
            )
            raise
        finally:
            session.close()
