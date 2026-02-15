import logging
from datetime import datetime, timezone

import ccxt

from app.config import get_settings
from app.database import SessionLocal
from app.models.trading import PriceHistory

logger = logging.getLogger(__name__)
settings = get_settings()


class PriceCollectorService:
    """Service for collecting cryptocurrency price data from Binance."""

    def __init__(self) -> None:
        self.exchange = ccxt.binance(
            {
                "apiKey": settings.binance_api_key or None,
                "secret": settings.binance_api_secret or None,
                "enableRateLimit": True,
            }
        )

    async def get_current_price(self, symbol: str) -> dict:
        """Fetch current OHLCV data from Binance for a given symbol.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT').

        Returns:
            Dictionary with OHLCV price data.

        Raises:
            ccxt.NetworkError: If there is a network connectivity issue.
            ccxt.ExchangeError: If the exchange returns an error.
        """
        try:
            logger.info("Fetching OHLCV data for %s from Binance", symbol)

            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe="5m", limit=1)

            if not ohlcv:
                raise ValueError(f"No OHLCV data returned for {symbol}")

            candle = ohlcv[0]
            # candle format: [timestamp, open, high, low, close, volume]
            price_data = {
                "symbol": symbol,
                "timestamp": datetime.fromtimestamp(
                    candle[0] / 1000, tz=timezone.utc
                ),
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
                "price": float(candle[4]),  # use close as current price
            }

            logger.info(
                "Fetched price for %s: %s", symbol, price_data["price"]
            )
            return price_data

        except ccxt.NetworkError as e:
            logger.error("Network error fetching %s price: %s", symbol, e)
            raise
        except ccxt.ExchangeError as e:
            logger.error("Exchange error fetching %s price: %s", symbol, e)
            raise
        except Exception as e:
            logger.error(
                "Unexpected error fetching %s price: %s", symbol, e
            )
            raise

    def save_price(self, price_data: dict) -> PriceHistory:
        """Save price data to the database.

        Args:
            price_data: Dictionary containing OHLCV price data.

        Returns:
            The saved PriceHistory instance.
        """
        session = SessionLocal()
        try:
            price_record = PriceHistory(
                symbol=price_data["symbol"],
                price=price_data["price"],
                volume=price_data["volume"],
                timestamp=price_data["timestamp"],
                high=price_data["high"],
                low=price_data["low"],
                open=price_data["open"],
                close=price_data["close"],
            )
            session.add(price_record)
            session.commit()
            session.refresh(price_record)

            logger.info(
                "Saved price record id=%d for %s at %s",
                price_record.id,
                price_record.symbol,
                price_record.price,
            )
            return price_record

        except Exception as e:
            session.rollback()
            logger.error("Error saving price data: %s", e)
            raise
        finally:
            session.close()
