"""Backtesting service for strategy evaluation on historical data.

Replays historical price and sentiment data to simulate what would have
happened if the trading strategy had been active during a past period.
Useful for testing different strategy parameters (RSI thresholds,
position sizes, SL/TP levels) without risking capital.
"""

import logging
import math
from datetime import datetime, timezone

from sqlalchemy import asc
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.trading import PriceHistory, SentimentScore, SignalAction

logger = logging.getLogger(__name__)

# Default strategy parameters matching SignalGenerator's logic
DEFAULT_STRATEGY_PARAMS = {
    "rsi_oversold": 35,
    "rsi_overbought": 65,
    "position_size": 0.1,
    "stop_loss_percent": 3.0,
    "take_profit_percent": 5.0,
    "initial_balance": 10000.0,
}


class Backtester:
    """Simulates trading strategy performance on historical data.

    Uses the same signal logic as SignalGenerator (RSI + sentiment + MA50)
    but applied to historical data. Allows tuning strategy parameters to
    find optimal configurations.

    The backtest processes prices chronologically, generating signals at
    each price point and executing simulated trades with SL/TP enforcement.
    """

    def run_backtest(
        self,
        start_date: datetime,
        end_date: datetime,
        strategy_params: dict | None = None,
    ) -> dict:
        """Run a backtest over a historical period.

        Fetches price history and sentiment data from the database,
        calculates indicators, generates signals, and simulates trades
        for the specified date range.

        Args:
            start_date: Start of the backtest period (inclusive).
            end_date: End of the backtest period (inclusive).
            strategy_params: Optional dict overriding default strategy
                parameters (rsi_oversold, rsi_overbought, position_size,
                stop_loss_percent, take_profit_percent, initial_balance).

        Returns:
            Dictionary with backtest results including:
                - trades: list of simulated trades
                - metrics: performance statistics (total_pnl, win_rate, etc.)
                - parameters: strategy params used
        """
        params = {**DEFAULT_STRATEGY_PARAMS, **(strategy_params or {})}

        session = SessionLocal()
        try:
            return self._execute_backtest(session, start_date, end_date, params)
        finally:
            session.close()

    def _execute_backtest(
        self,
        session: Session,
        start_date: datetime,
        end_date: datetime,
        params: dict,
    ) -> dict:
        """Core backtest execution logic.

        Processes prices sequentially, maintaining a rolling window for
        indicator calculation. At each price point:
        1. Calculate RSI from the last 14+ prices
        2. Calculate MA50 from the last 50 prices
        3. Look up sentiment near that timestamp
        4. Generate a signal using the strategy rules
        5. Execute trades and check SL/TP

        Args:
            session: Active database session.
            start_date: Backtest start date.
            end_date: Backtest end date.
            params: Strategy parameters.

        Returns:
            Complete backtest results dict.
        """
        # Fetch historical prices for the period
        # We need extra data before start_date for indicator warm-up (50 periods for MA50)
        prices = (
            session.query(PriceHistory)
            .filter(
                PriceHistory.symbol == "BTC/USDT",
                PriceHistory.timestamp >= start_date,
                PriceHistory.timestamp <= end_date,
            )
            .order_by(asc(PriceHistory.timestamp))
            .all()
        )

        if len(prices) < 50:
            logger.warning(
                "Insufficient price data for backtest: %d records (need >= 50)",
                len(prices),
            )
            return {
                "status": "error",
                "reason": f"Insufficient data: {len(prices)} price records (need >= 50)",
                "parameters": params,
                "trades": [],
                "metrics": {},
            }

        # Fetch sentiment scores for the period
        sentiment_scores = (
            session.query(SentimentScore)
            .filter(
                SentimentScore.symbol == "BTC",
                SentimentScore.timestamp >= start_date,
                SentimentScore.timestamp <= end_date,
            )
            .order_by(asc(SentimentScore.timestamp))
            .all()
        )

        # Index sentiments by hour for quick lookup
        sentiment_by_hour: dict[str, list[float]] = {}
        for s in sentiment_scores:
            hour_key = s.timestamp.strftime("%Y-%m-%d-%H")
            sentiment_by_hour.setdefault(hour_key, []).append(s.score)

        # Simulate trading
        trades: list[dict] = []
        open_trade: dict | None = None
        price_values = [p.close for p in prices]

        for i in range(50, len(prices)):
            current_price = prices[i].close
            timestamp = prices[i].timestamp

            # Calculate RSI (14-period) from the closing prices up to this point
            window = price_values[max(0, i - 250) : i + 1]
            rsi = self._calculate_rsi(window, period=14)

            # Calculate MA50
            ma50 = sum(price_values[i - 49 : i + 1]) / 50

            # Look up sentiment near this timestamp
            hour_key = timestamp.strftime("%Y-%m-%d-%H")
            hour_sentiments = sentiment_by_hour.get(hour_key, [])
            sentiment = (
                sum(hour_sentiments) / len(hour_sentiments)
                if hour_sentiments
                else None
            )

            # Generate signal using strategy rules
            signal = self._evaluate_signal(
                rsi, sentiment, current_price, ma50, params
            )

            # Check SL/TP on open trade first
            if open_trade is not None:
                sl_price = open_trade["entry_price"] * (
                    1 - params["stop_loss_percent"] / 100
                )
                tp_price = open_trade["entry_price"] * (
                    1 + params["take_profit_percent"] / 100
                )

                if current_price <= sl_price:
                    # Stop-loss triggered
                    pnl = (current_price - open_trade["entry_price"]) * params["position_size"]
                    pnl_pct = ((current_price - open_trade["entry_price"]) / open_trade["entry_price"]) * 100
                    open_trade.update({
                        "exit_price": current_price,
                        "exit_time": timestamp.isoformat(),
                        "pnl": round(pnl, 2),
                        "pnl_percent": round(pnl_pct, 2),
                        "exit_reason": "stop_loss",
                    })
                    trades.append(open_trade)
                    open_trade = None
                    continue

                if current_price >= tp_price:
                    # Take-profit triggered
                    pnl = (current_price - open_trade["entry_price"]) * params["position_size"]
                    pnl_pct = ((current_price - open_trade["entry_price"]) / open_trade["entry_price"]) * 100
                    open_trade.update({
                        "exit_price": current_price,
                        "exit_time": timestamp.isoformat(),
                        "pnl": round(pnl, 2),
                        "pnl_percent": round(pnl_pct, 2),
                        "exit_reason": "take_profit",
                    })
                    trades.append(open_trade)
                    open_trade = None
                    continue

            # Execute trades based on signal
            if open_trade is None and signal == SignalAction.BUY:
                open_trade = {
                    "entry_price": current_price,
                    "entry_time": timestamp.isoformat(),
                    "quantity": params["position_size"],
                    "rsi": rsi,
                    "sentiment": sentiment,
                }
            elif open_trade is not None and signal == SignalAction.SELL:
                pnl = (current_price - open_trade["entry_price"]) * params["position_size"]
                pnl_pct = ((current_price - open_trade["entry_price"]) / open_trade["entry_price"]) * 100
                open_trade.update({
                    "exit_price": current_price,
                    "exit_time": timestamp.isoformat(),
                    "pnl": round(pnl, 2),
                    "pnl_percent": round(pnl_pct, 2),
                    "exit_reason": "sell_signal",
                })
                trades.append(open_trade)
                open_trade = None

        # If a trade is still open at end of backtest, mark it as unclosed
        if open_trade is not None:
            last_price = prices[-1].close
            pnl = (last_price - open_trade["entry_price"]) * params["position_size"]
            pnl_pct = ((last_price - open_trade["entry_price"]) / open_trade["entry_price"]) * 100
            open_trade.update({
                "exit_price": last_price,
                "exit_time": prices[-1].timestamp.isoformat(),
                "pnl": round(pnl, 2),
                "pnl_percent": round(pnl_pct, 2),
                "exit_reason": "backtest_end",
            })
            trades.append(open_trade)

        # Calculate performance metrics
        metrics = self._calculate_metrics(trades, params["initial_balance"])

        logger.info(
            "Backtest complete: %d trades, total P&L=$%.2f, win_rate=%.1f%%",
            len(trades),
            metrics.get("total_pnl", 0),
            metrics.get("win_rate", 0),
        )

        return {
            "status": "completed",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
            "data_points": len(prices),
            "parameters": params,
            "trades": trades,
            "metrics": metrics,
        }

    def _evaluate_signal(
        self,
        rsi: float | None,
        sentiment: float | None,
        price: float,
        ma50: float,
        params: dict,
    ) -> SignalAction:
        """Apply the signal generation rules to determine BUY/SELL/HOLD.

        Mirrors the logic in SignalGenerator:
        - BUY: RSI < oversold AND sentiment > 0 AND price < MA50
        - SELL: RSI > overbought AND sentiment < 0 AND price > MA50
        - HOLD: otherwise

        Args:
            rsi: Current RSI value (or None if not calculable).
            sentiment: Current sentiment score (-1 to 1, or None).
            price: Current market price.
            ma50: 50-period moving average.
            params: Strategy parameters with RSI thresholds.

        Returns:
            SignalAction (BUY, SELL, or HOLD).
        """
        buy_conditions = 0
        sell_conditions = 0

        if rsi is not None:
            if rsi < params["rsi_oversold"]:
                buy_conditions += 1
            if rsi > params["rsi_overbought"]:
                sell_conditions += 1

        if sentiment is not None:
            if sentiment > 0:
                buy_conditions += 1
            if sentiment < 0:
                sell_conditions += 1

        if price < ma50:
            buy_conditions += 1
        if price > ma50:
            sell_conditions += 1

        if buy_conditions == 3:
            return SignalAction.BUY
        if sell_conditions == 3:
            return SignalAction.SELL
        return SignalAction.HOLD

    def _calculate_rsi(self, prices: list[float], period: int = 14) -> float | None:
        """Calculate RSI from a list of closing prices.

        Uses the standard RSI formula with exponential moving average
        of gains and losses over the specified period.

        Args:
            prices: List of closing prices (oldest first).
            period: RSI lookback period (default 14).

        Returns:
            RSI value (0-100) or None if insufficient data.
        """
        if len(prices) < period + 1:
            return None

        # Calculate price changes
        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

        # Initial average gain/loss
        gains = [max(d, 0) for d in deltas[:period]]
        losses = [abs(min(d, 0)) for d in deltas[:period]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        # Smooth with exponential moving average
        for d in deltas[period:]:
            avg_gain = (avg_gain * (period - 1) + max(d, 0)) / period
            avg_loss = (avg_loss * (period - 1) + abs(min(d, 0))) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)

    def _calculate_metrics(
        self, trades: list[dict], initial_balance: float
    ) -> dict:
        """Calculate performance metrics from completed backtest trades.

        Args:
            trades: List of trade dicts with 'pnl' values.
            initial_balance: Starting balance for the backtest.

        Returns:
            Dictionary with total_pnl, win_rate, max_drawdown,
            sharpe_ratio, and other statistics.
        """
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "best_trade": 0.0,
                "worst_trade": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": None,
                "final_balance": initial_balance,
            }

        pnl_values = [t["pnl"] for t in trades]
        wins = [p for p in pnl_values if p > 0]
        losses = [p for p in pnl_values if p <= 0]

        total_pnl = sum(pnl_values)

        # Max drawdown from cumulative P&L
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        for pnl in pnl_values:
            cumulative += pnl
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd

        # Sharpe ratio (annualized, assuming ~1095 trades/year)
        sharpe = None
        if len(pnl_values) >= 2:
            mean_pnl = total_pnl / len(pnl_values)
            variance = sum((p - mean_pnl) ** 2 for p in pnl_values) / (len(pnl_values) - 1)
            std_pnl = math.sqrt(variance)
            if std_pnl > 0:
                sharpe = round((mean_pnl / std_pnl) * math.sqrt(1095), 4)

        return {
            "total_trades": len(trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": round((len(wins) / len(trades)) * 100, 2),
            "total_pnl": round(total_pnl, 2),
            "avg_win": round(sum(wins) / len(wins), 2) if wins else 0.0,
            "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0.0,
            "best_trade": round(max(pnl_values), 2),
            "worst_trade": round(min(pnl_values), 2),
            "max_drawdown": round(max_dd, 2),
            "sharpe_ratio": sharpe,
            "final_balance": round(initial_balance + total_pnl, 2),
        }
