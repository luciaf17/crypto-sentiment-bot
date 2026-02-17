"""Backtesting service for strategy evaluation on historical data.

Replays historical price and sentiment data to simulate what would have
happened if the trading strategy had been active during a past period.
Useful for testing different strategy parameters (RSI thresholds,
position sizes, SL/TP levels) without risking capital.

Key design decisions to avoid lookahead bias:
- Indicators are calculated using only data available *up to* the current
  bar — never future data.
- Prices are processed in strict chronological order.
- Sentiment lookup uses the closest score *before or at* the current time.
"""

import logging
import math
from datetime import datetime, timedelta, timezone

from sqlalchemy import asc
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.backtest import BacktestRun
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

# Minimum number of price records required before we can generate signals.
# MA(50) needs 50 data points; we add a small buffer for RSI warm-up.
MIN_WARMUP_BARS = 50


class Backtester:
    """Simulates trading strategy performance on historical data.

    Uses the same signal logic as SignalGenerator (RSI + sentiment + MA50)
    but applied to historical data.  Allows tuning strategy parameters to
    find optimal configurations.

    The backtest processes prices chronologically, generating signals at
    each price point and executing simulated trades with SL/TP enforcement.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_backtest(
        self,
        symbol: str = "BTC/USDT",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        strategy_params: dict | None = None,
        save: bool = True,
    ) -> dict:
        """Run a backtest over a historical period.

        Fetches price history and sentiment data from the database,
        calculates indicators, generates signals, and simulates trades
        for the specified date range.

        Args:
            symbol: Trading pair to backtest (e.g. "BTC/USDT").
            start_date: Start of the backtest period (inclusive).
                Falls back to 30 days ago when *None*.
            end_date: End of the backtest period (inclusive).
                Falls back to now when *None*.
            strategy_params: Optional dict overriding default strategy
                parameters.  Accepts both backtester naming
                (rsi_oversold/rsi_overbought) and strategy naming
                (rsi_buy/rsi_sell) — the latter is auto-mapped.
            save: Whether to persist the result to the database.

        Returns:
            Dictionary with backtest results including trades, metrics,
            equity_curve, and parameters.
        """
        if start_date is None:
            start_date = datetime.now(timezone.utc) - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now(timezone.utc)

        mapped = self._map_strategy_params(strategy_params or {})
        params = {**DEFAULT_STRATEGY_PARAMS, **mapped}

        session = SessionLocal()
        try:
            result = self._execute_backtest(
                session, symbol, start_date, end_date, params
            )

            # Persist to database if requested
            if save:
                run = BacktestRun(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    parameters=params,
                    metrics=result.get("metrics", {}),
                    trades=result.get("trades", []),
                    equity_curve=result.get("equity_curve", []),
                    data_points=result.get("data_points", 0),
                    status=result.get("status", "completed"),
                    error_reason=result.get("error_reason"),
                )
                session.add(run)
                session.commit()
                session.refresh(run)
                result["id"] = run.id
                result["created_at"] = run.created_at.isoformat()

            return result
        finally:
            session.close()

    @staticmethod
    def get_result(backtest_id: int) -> BacktestRun | None:
        """Retrieve a saved backtest run by ID."""
        session = SessionLocal()
        try:
            return session.get(BacktestRun, backtest_id)
        finally:
            session.close()

    @staticmethod
    def get_results_for_compare(ids: list[int]) -> list[BacktestRun]:
        """Retrieve multiple saved backtest runs for comparison."""
        session = SessionLocal()
        try:
            return (
                session.query(BacktestRun)
                .filter(BacktestRun.id.in_(ids))
                .all()
            )
        finally:
            session.close()

    def calculate_metrics(
        self, trades: list[dict], initial_balance: float
    ) -> dict:
        """Calculate comprehensive performance metrics from backtest trades.

        Computes win/loss statistics, P&L totals, drawdown analysis,
        risk-adjusted returns (Sharpe ratio), and trade duration metrics.

        Args:
            trades: List of trade dicts — each must contain at least
                ``pnl``, ``entry_time``, ``exit_time``.
            initial_balance: Starting balance for the backtest.

        Returns:
            Dictionary of all computed metrics.
        """
        if not trades:
            return self._empty_metrics(initial_balance)

        pnl_values = [t["pnl"] for t in trades]
        wins = [p for p in pnl_values if p > 0]
        losses = [p for p in pnl_values if p <= 0]

        total_pnl = sum(pnl_values)
        total_pnl_percent = (total_pnl / initial_balance) * 100 if initial_balance else 0.0

        # --- Profit factor ---
        gross_profit = sum(wins) if wins else 0.0
        gross_loss = abs(sum(losses)) if losses else 0.0
        profit_factor = (
            round(gross_profit / gross_loss, 4)
            if gross_loss > 0
            else None
        )

        # --- Max drawdown (from cumulative equity) ---
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

        max_dd_pct = (max_dd / initial_balance) * 100 if initial_balance else 0.0

        # --- Sharpe ratio (annualised, ~1095 trade-periods/year) ---
        sharpe = None
        if len(pnl_values) >= 2:
            mean_pnl = total_pnl / len(pnl_values)
            variance = sum((p - mean_pnl) ** 2 for p in pnl_values) / (
                len(pnl_values) - 1
            )
            std_pnl = math.sqrt(variance)
            if std_pnl > 0:
                sharpe = round((mean_pnl / std_pnl) * math.sqrt(1095), 4)

        # --- Average hold duration ---
        durations_hours: list[float] = []
        for t in trades:
            entry = t.get("entry_time")
            exit_ = t.get("exit_time")
            if entry and exit_:
                try:
                    dt_entry = datetime.fromisoformat(entry)
                    dt_exit = datetime.fromisoformat(exit_)
                    durations_hours.append(
                        (dt_exit - dt_entry).total_seconds() / 3600
                    )
                except (ValueError, TypeError):
                    pass

        avg_hold = (
            round(sum(durations_hours) / len(durations_hours), 2)
            if durations_hours
            else None
        )

        return {
            "total_trades": len(trades),
            "winning_trades": len(wins),
            "losing_trades": len(losses),
            "win_rate": round((len(wins) / len(trades)) * 100, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_percent": round(total_pnl_percent, 2),
            "avg_win": round(sum(wins) / len(wins), 2) if wins else 0.0,
            "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0.0,
            "profit_factor": profit_factor,
            "max_drawdown": round(max_dd, 2),
            "max_drawdown_percent": round(max_dd_pct, 2),
            "sharpe_ratio": sharpe,
            "best_trade": round(max(pnl_values), 2),
            "worst_trade": round(min(pnl_values), 2),
            "avg_hold_duration_hours": avg_hold,
            "final_balance": round(initial_balance + total_pnl, 2),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _execute_backtest(
        self,
        session: Session,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        params: dict,
    ) -> dict:
        """Core backtest execution logic.

        Processes prices sequentially, maintaining a rolling window for
        indicator calculation.  At each price point:
        1. Calculate RSI from the last 14+ prices (no future data)
        2. Calculate MA50 from the last 50 prices
        3. Look up sentiment nearest to that timestamp
        4. Generate a signal using the strategy rules
        5. Check SL/TP on open positions, then evaluate new signal

        Args:
            session: Active database session.
            symbol: Trading pair symbol.
            start_date: Backtest start date.
            end_date: Backtest end date.
            params: Merged strategy parameters.

        Returns:
            Complete backtest results dict.
        """
        # Determine the base currency for sentiment lookup
        # (PriceHistory uses "BTC/USDT", SentimentScore uses "BTC")
        base_symbol = symbol.split("/")[0] if "/" in symbol else symbol

        # ---------------------------------------------------------------
        # 1. Fetch historical price data
        # ---------------------------------------------------------------
        prices = (
            session.query(PriceHistory)
            .filter(
                PriceHistory.symbol == symbol,
                PriceHistory.timestamp >= start_date,
                PriceHistory.timestamp <= end_date,
            )
            .order_by(asc(PriceHistory.timestamp))
            .all()
        )

        if len(prices) < MIN_WARMUP_BARS:
            reason = (
                f"Insufficient data: {len(prices)} price records "
                f"(need >= {MIN_WARMUP_BARS})"
            )
            logger.warning("Backtest aborted — %s", reason)
            return {
                "status": "error",
                "error_reason": reason,
                "symbol": symbol,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "data_points": len(prices),
                "parameters": params,
                "trades": [],
                "metrics": self._empty_metrics(params["initial_balance"]),
                "equity_curve": [],
            }

        # ---------------------------------------------------------------
        # 2. Fetch sentiment scores for the period
        # ---------------------------------------------------------------
        sentiment_scores = (
            session.query(SentimentScore)
            .filter(
                SentimentScore.symbol == base_symbol,
                SentimentScore.timestamp >= start_date,
                SentimentScore.timestamp <= end_date,
            )
            .order_by(asc(SentimentScore.timestamp))
            .all()
        )

        # Index sentiments by hour key for O(1) lookup
        sentiment_by_hour: dict[str, list[float]] = {}
        for s in sentiment_scores:
            hour_key = s.timestamp.strftime("%Y-%m-%d-%H")
            sentiment_by_hour.setdefault(hour_key, []).append(s.score)

        logger.info(
            "Backtest data loaded: %d prices, %d sentiment records "
            "(%s → %s) for %s",
            len(prices),
            len(sentiment_scores),
            start_date.isoformat(),
            end_date.isoformat(),
            symbol,
        )

        # ---------------------------------------------------------------
        # 3. Walk through prices chronologically
        # ---------------------------------------------------------------
        trades: list[dict] = []
        open_trade: dict | None = None
        price_values = [p.close for p in prices]
        initial_balance = params["initial_balance"]
        balance = initial_balance
        equity_curve: list[dict] = []

        for i in range(MIN_WARMUP_BARS, len(prices)):
            current_price = prices[i].close
            timestamp = prices[i].timestamp

            # -- Technical indicators (only past data) --
            window = price_values[max(0, i - 250) : i + 1]
            rsi = self._calculate_rsi(window, period=14)
            ma50 = sum(price_values[i - 49 : i + 1]) / 50

            # -- Sentiment lookup (closest hour) --
            hour_key = timestamp.strftime("%Y-%m-%d-%H")
            hour_sentiments = sentiment_by_hour.get(hour_key, [])
            sentiment = (
                sum(hour_sentiments) / len(hour_sentiments)
                if hour_sentiments
                else None
            )

            # -- Generate signal --
            signal = self._evaluate_signal(
                rsi, sentiment, current_price, ma50, params
            )

            # -- Check SL/TP on open trade before evaluating new signals --
            if open_trade is not None:
                sl_price = open_trade["entry_price"] * (
                    1 - params["stop_loss_percent"] / 100
                )
                tp_price = open_trade["entry_price"] * (
                    1 + params["take_profit_percent"] / 100
                )

                if current_price <= sl_price:
                    pnl, pnl_pct = self._calc_pnl(
                        open_trade["entry_price"],
                        current_price,
                        params["position_size"],
                    )
                    open_trade.update({
                        "exit_price": current_price,
                        "exit_time": timestamp.isoformat(),
                        "pnl": pnl,
                        "pnl_percent": pnl_pct,
                        "exit_reason": "stop_loss",
                    })
                    trades.append(open_trade)
                    balance += pnl
                    logger.debug(
                        "SL hit @ %s: entry=%.2f exit=%.2f pnl=%.2f",
                        timestamp, open_trade["entry_price"], current_price, pnl,
                    )
                    open_trade = None
                    equity_curve.append({
                        "timestamp": timestamp.isoformat(),
                        "balance": round(balance, 2),
                    })
                    continue

                if current_price >= tp_price:
                    pnl, pnl_pct = self._calc_pnl(
                        open_trade["entry_price"],
                        current_price,
                        params["position_size"],
                    )
                    open_trade.update({
                        "exit_price": current_price,
                        "exit_time": timestamp.isoformat(),
                        "pnl": pnl,
                        "pnl_percent": pnl_pct,
                        "exit_reason": "take_profit",
                    })
                    trades.append(open_trade)
                    balance += pnl
                    logger.debug(
                        "TP hit @ %s: entry=%.2f exit=%.2f pnl=%.2f",
                        timestamp, open_trade["entry_price"], current_price, pnl,
                    )
                    open_trade = None
                    equity_curve.append({
                        "timestamp": timestamp.isoformat(),
                        "balance": round(balance, 2),
                    })
                    continue

            # -- Execute trades based on signal --
            if open_trade is None and signal == SignalAction.BUY:
                open_trade = {
                    "entry_price": current_price,
                    "entry_time": timestamp.isoformat(),
                    "quantity": params["position_size"],
                    "rsi": rsi,
                    "sentiment": sentiment,
                }
                logger.debug(
                    "BUY @ %s: price=%.2f rsi=%s sentiment=%s",
                    timestamp, current_price, rsi, sentiment,
                )
            elif open_trade is not None and signal == SignalAction.SELL:
                pnl, pnl_pct = self._calc_pnl(
                    open_trade["entry_price"],
                    current_price,
                    params["position_size"],
                )
                open_trade.update({
                    "exit_price": current_price,
                    "exit_time": timestamp.isoformat(),
                    "pnl": pnl,
                    "pnl_percent": pnl_pct,
                    "exit_reason": "sell_signal",
                })
                trades.append(open_trade)
                balance += pnl
                logger.debug(
                    "SELL @ %s: entry=%.2f exit=%.2f pnl=%.2f",
                    timestamp, open_trade["entry_price"], current_price, pnl,
                )
                open_trade = None

            # Record equity curve point periodically (every ~12 bars ≈ 1h
            # when data is collected every 5 min)
            if i % 12 == 0:
                unrealised = 0.0
                if open_trade is not None:
                    unrealised = (
                        current_price - open_trade["entry_price"]
                    ) * params["position_size"]
                equity_curve.append({
                    "timestamp": timestamp.isoformat(),
                    "balance": round(balance + unrealised, 2),
                })

        # ---------------------------------------------------------------
        # 4. Close any position still open at end of period
        # ---------------------------------------------------------------
        if open_trade is not None:
            last_price = prices[-1].close
            pnl, pnl_pct = self._calc_pnl(
                open_trade["entry_price"],
                last_price,
                params["position_size"],
            )
            open_trade.update({
                "exit_price": last_price,
                "exit_time": prices[-1].timestamp.isoformat(),
                "pnl": pnl,
                "pnl_percent": pnl_pct,
                "exit_reason": "backtest_end",
            })
            trades.append(open_trade)
            balance += pnl

        # Final equity point
        if prices:
            equity_curve.append({
                "timestamp": prices[-1].timestamp.isoformat(),
                "balance": round(balance, 2),
            })

        # ---------------------------------------------------------------
        # 5. Compute metrics
        # ---------------------------------------------------------------
        metrics = self.calculate_metrics(trades, initial_balance)

        logger.info(
            "Backtest complete for %s: %d trades, total P&L=$%.2f (%.2f%%), "
            "win_rate=%.1f%%, max_dd=$%.2f, sharpe=%s",
            symbol,
            len(trades),
            metrics["total_pnl"],
            metrics["total_pnl_percent"],
            metrics["win_rate"],
            metrics["max_drawdown"],
            metrics.get("sharpe_ratio"),
        )

        return {
            "status": "completed",
            "symbol": symbol,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "data_points": len(prices),
            "parameters": params,
            "trades": trades,
            "metrics": metrics,
            "equity_curve": equity_curve,
        }

    # ------------------------------------------------------------------
    # Signal evaluation (mirrors SignalGenerator rules)
    # ------------------------------------------------------------------

    @staticmethod
    def _evaluate_signal(
        rsi: float | None,
        sentiment: float | None,
        price: float,
        ma50: float,
        params: dict,
    ) -> SignalAction:
        """Apply the signal generation rules to determine BUY/SELL/HOLD.

        Mirrors the logic in SignalGenerator:
        - BUY:  RSI < oversold  AND sentiment > 0 AND price < MA50
        - SELL: RSI > overbought AND sentiment < 0 AND price > MA50
        - HOLD: otherwise
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

    # ------------------------------------------------------------------
    # RSI calculation (self-contained, no pandas dependency)
    # ------------------------------------------------------------------

    @staticmethod
    def _calculate_rsi(prices: list[float], period: int = 14) -> float | None:
        """Calculate RSI using Wilder smoothing.

        Args:
            prices: Closing prices (oldest first).
            period: Lookback period (default 14).

        Returns:
            RSI value (0-100) or None if insufficient data.
        """
        if len(prices) < period + 1:
            return None

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]

        gains = [max(d, 0) for d in deltas[:period]]
        losses = [abs(min(d, 0)) for d in deltas[:period]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        for d in deltas[period:]:
            avg_gain = (avg_gain * (period - 1) + max(d, 0)) / period
            avg_loss = (avg_loss * (period - 1) + abs(min(d, 0))) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return round(100 - (100 / (1 + rs)), 2)

    # ------------------------------------------------------------------
    # P&L helper
    # ------------------------------------------------------------------

    @staticmethod
    def _calc_pnl(
        entry_price: float, exit_price: float, quantity: float
    ) -> tuple[float, float]:
        """Return (pnl_absolute, pnl_percent) rounded to 2 decimals."""
        pnl = (exit_price - entry_price) * quantity
        pnl_pct = (
            ((exit_price - entry_price) / entry_price) * 100
            if entry_price
            else 0.0
        )
        return round(pnl, 2), round(pnl_pct, 2)

    # ------------------------------------------------------------------
    # Empty metrics template
    # ------------------------------------------------------------------

    @staticmethod
    def _map_strategy_params(raw: dict) -> dict:
        """Map Strategy Tuner parameter names to backtester names.

        The Strategy system uses ``rsi_buy`` / ``rsi_sell`` while the
        backtester internally uses ``rsi_oversold`` / ``rsi_overbought``.
        This helper accepts either convention and returns a dict that the
        backtester can merge directly into its defaults.
        """
        mapped = dict(raw)
        if "rsi_buy" in mapped and "rsi_oversold" not in mapped:
            mapped["rsi_oversold"] = mapped.pop("rsi_buy")
        if "rsi_sell" in mapped and "rsi_overbought" not in mapped:
            mapped["rsi_overbought"] = mapped.pop("rsi_sell")
        return mapped

    @staticmethod
    def _empty_metrics(initial_balance: float) -> dict:
        """Return a zeroed-out metrics dict for when there are no trades."""
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "total_pnl_percent": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": None,
            "max_drawdown": 0.0,
            "max_drawdown_percent": 0.0,
            "sharpe_ratio": None,
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "avg_hold_duration_hours": None,
            "final_balance": initial_balance,
        }
