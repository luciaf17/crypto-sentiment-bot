"""Load recent OHLCV candles into price_history.

Fetches recent candles from Binance via ccxt and stores them in the
price_history table, skipping any timestamps already present.
"""

import argparse
from datetime import datetime, timezone

import ccxt

from app.database import SessionLocal
from app.models.trading import PriceHistory


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load recent OHLCV candles into price_history."
    )
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="5m")
    parser.add_argument("--limit", type=int, default=500)
    return parser.parse_args()


def _to_datetime(ts_ms: int) -> datetime:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)


def main() -> int:
    args = _parse_args()
    exchange = ccxt.binance({"enableRateLimit": True})

    try:
        ohlcv = exchange.fetch_ohlcv(
            args.symbol, timeframe=args.timeframe, limit=args.limit
        )
        if not ohlcv:
            print("No OHLCV data returned.")
            return 1

        timestamps = [_to_datetime(candle[0]) for candle in ohlcv]
        min_dt = min(timestamps)
        max_dt = max(timestamps)

        session = SessionLocal()
        try:
            existing_rows = (
                session.query(PriceHistory.timestamp)
                .filter(
                    PriceHistory.symbol == args.symbol,
                    PriceHistory.timestamp >= min_dt,
                    PriceHistory.timestamp <= max_dt,
                )
                .all()
            )
            existing_ts = {row[0] for row in existing_rows}

            new_rows = []
            for candle in ohlcv:
                ts = _to_datetime(candle[0])
                if ts in existing_ts:
                    continue

                new_rows.append(
                    PriceHistory(
                        symbol=args.symbol,
                        timestamp=ts,
                        open=float(candle[1]),
                        high=float(candle[2]),
                        low=float(candle[3]),
                        close=float(candle[4]),
                        price=float(candle[4]),
                        volume=float(candle[5]),
                    )
                )

            if not new_rows:
                print("No new candles to insert.")
                return 0

            session.bulk_save_objects(new_rows)
            session.commit()
            print(f"Inserted {len(new_rows)} candles for {args.symbol}.")
            return 0
        finally:
            session.close()
    finally:
        if hasattr(exchange, "close"):
            exchange.close()


if __name__ == "__main__":
    raise SystemExit(main())
