"""API endpoints for paper trade management and performance metrics."""

import math
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.trading import Trade, TradeStatus
from app.schemas.trade import TradeResponse, TradeStatsResponse
from app.services.paper_trader import INITIAL_BALANCE

router = APIRouter(prefix="/trades", tags=["trades"])


@router.get("/active", response_model=list[TradeResponse])
def get_active_trades(
    db: Session = Depends(get_db_session),
) -> list[Trade]:
    """Return all currently open trades."""
    return (
        db.query(Trade)
        .filter(Trade.status == TradeStatus.OPEN)
        .order_by(desc(Trade.opened_at))
        .all()
    )


@router.get("/history", response_model=list[TradeResponse])
def get_trade_history(
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db_session),
) -> list[Trade]:
    """Return closed trades with pagination."""
    return (
        db.query(Trade)
        .filter(Trade.status == TradeStatus.CLOSED)
        .order_by(desc(Trade.closed_at))
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/stats", response_model=TradeStatsResponse)
def get_trade_stats(
    db: Session = Depends(get_db_session),
) -> TradeStatsResponse:
    """Return performance metrics for all paper trades.

    Calculates win rate, total P&L, average win/loss, best/worst trade,
    max drawdown, Sharpe ratio, and current balance.
    """
    closed_trades = (
        db.query(Trade)
        .filter(Trade.status == TradeStatus.CLOSED)
        .order_by(Trade.closed_at)
        .all()
    )

    open_count = (
        db.query(Trade)
        .filter(Trade.status == TradeStatus.OPEN)
        .count()
    )

    total = len(closed_trades)

    if total == 0:
        return TradeStatsResponse(
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_pnl=0.0,
            total_pnl_percent=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            best_trade=0.0,
            worst_trade=0.0,
            max_drawdown=0.0,
            sharpe_ratio=None,
            current_balance=INITIAL_BALANCE,
            open_trades=open_count,
        )

    # Separate winning and losing trades
    wins = [t for t in closed_trades if t.pnl is not None and t.pnl > 0]
    losses = [t for t in closed_trades if t.pnl is not None and t.pnl <= 0]
    pnl_values = [t.pnl for t in closed_trades if t.pnl is not None]

    total_pnl = sum(pnl_values)
    win_rate = (len(wins) / total) * 100 if total > 0 else 0.0

    avg_win = sum(t.pnl for t in wins) / len(wins) if wins else 0.0
    avg_loss = sum(t.pnl for t in losses) / len(losses) if losses else 0.0

    best_trade = max(pnl_values) if pnl_values else 0.0
    worst_trade = min(pnl_values) if pnl_values else 0.0

    # Max drawdown: largest peak-to-trough decline in cumulative P&L
    max_drawdown = _calculate_max_drawdown(pnl_values)

    # Sharpe ratio: mean(returns) / std(returns), annualized
    sharpe = _calculate_sharpe_ratio(pnl_values)

    # Total P&L as percentage of initial balance
    total_pnl_percent = (total_pnl / INITIAL_BALANCE) * 100

    return TradeStatsResponse(
        total_trades=total,
        winning_trades=len(wins),
        losing_trades=len(losses),
        win_rate=round(win_rate, 2),
        total_pnl=round(total_pnl, 2),
        total_pnl_percent=round(total_pnl_percent, 2),
        avg_win=round(avg_win, 2),
        avg_loss=round(avg_loss, 2),
        best_trade=round(best_trade, 2),
        worst_trade=round(worst_trade, 2),
        max_drawdown=round(max_drawdown, 2),
        sharpe_ratio=round(sharpe, 4) if sharpe is not None else None,
        current_balance=round(INITIAL_BALANCE + total_pnl, 2),
        open_trades=open_count,
    )


def _calculate_max_drawdown(pnl_values: list[float]) -> float:
    """Calculate maximum drawdown from a sequence of P&L values.

    Drawdown is the largest decline from a peak in cumulative returns.
    A drawdown of 500 means at some point, the portfolio was $500 below
    its highest point.

    Args:
        pnl_values: Ordered list of individual trade P&L values.

    Returns:
        Maximum drawdown as a positive dollar amount (0 if no drawdown).
    """
    if not pnl_values:
        return 0.0

    cumulative = 0.0
    peak = 0.0
    max_dd = 0.0

    for pnl in pnl_values:
        cumulative += pnl
        if cumulative > peak:
            peak = cumulative
        drawdown = peak - cumulative
        if drawdown > max_dd:
            max_dd = drawdown

    return max_dd


def _calculate_sharpe_ratio(pnl_values: list[float]) -> float | None:
    """Calculate annualized Sharpe ratio from trade P&L values.

    Uses the simplified Sharpe formula: mean(returns) / std(returns),
    annualized by multiplying by sqrt(number_of_trades_per_year).

    Assumes roughly 3 trades per day (every 8 hours) → ~1095/year.
    Returns None if fewer than 2 trades (cannot compute std deviation).

    Args:
        pnl_values: List of individual trade P&L values.

    Returns:
        Annualized Sharpe ratio or None if insufficient data.
    """
    if len(pnl_values) < 2:
        return None

    mean_pnl = sum(pnl_values) / len(pnl_values)
    variance = sum((p - mean_pnl) ** 2 for p in pnl_values) / (len(pnl_values) - 1)
    std_pnl = math.sqrt(variance)

    if std_pnl == 0:
        return None

    # Annualize: assume ~1095 trades per year (3 per day)
    trades_per_year = 1095
    sharpe = (mean_pnl / std_pnl) * math.sqrt(trades_per_year)
    return sharpe
