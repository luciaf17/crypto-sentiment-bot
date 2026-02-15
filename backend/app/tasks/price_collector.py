import logging
from datetime import datetime, timezone

import ccxt.async_support as ccxt

from app.database import SessionLocal
from app.models.trading import PriceHistory

logger = logging.getLogger(__name__)


class PriceCollectorService:
    def __init__(self):
        self.exchange = ccxt.binance()

    async def get_current_price(self, symbol: str = "BTC/USDT") -> dict:
        """
        Fetch current OHLCV data from Binance
        
        Args:
            symbol: Trading pair (default: BTC/USDT)
            
        Returns:
            dict with keys: symbol, open, high, low, close, volume, timestamp
        """
        try:
            logger.info(f"Fetching price for {symbol}")
            
            # Fetch last 1 candle (5m timeframe)
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe="5m", limit=1)
            
            if not ohlcv:
                raise ValueError(f"No OHLCV data returned for {symbol}")
            
            # ohlcv format: [timestamp, open, high, low, close, volume]
            candle = ohlcv[0]
            
            price_data = {
                "symbol": symbol,
                "timestamp": datetime.fromtimestamp(candle[0] / 1000, tz=timezone.utc),
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "price": float(candle[4]),  # Use close as current price
                "volume": float(candle[5]),
            }
            
            logger.info(f"Fetched {symbol}: ${price_data['price']:.2f}")
            return price_data
            
        except ccxt.NetworkError as e:
            logger.error(f"Network error fetching {symbol}: {e}")
            raise
        except ccxt.ExchangeError as e:
            logger.error(f"Exchange error fetching {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching {symbol}: {e}")
            raise
        finally:
            await self.exchange.close()

    def save_price(self, price_data: dict) -> None:
        """
        Save price data to database
        
        Args:
            price_data: Dict containing OHLCV data
        """
        db = SessionLocal()
        try:
            price_record = PriceHistory(
                symbol=price_data["symbol"],
                timestamp=price_data["timestamp"],
                open=price_data["open"],
                high=price_data["high"],
                low=price_data["low"],
                close=price_data["close"],
                price=price_data["price"],
                volume=price_data["volume"],
            )
            
            db.add(price_record)
            db.commit()
            
            logger.info(f"Saved price to DB: {price_data['symbol']} @ ${price_data['price']:.2f}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error saving price to DB: {e}")
            raise
        finally:
            db.close()