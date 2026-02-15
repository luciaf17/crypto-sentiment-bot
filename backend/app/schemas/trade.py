"""Pydantic schemas for trade API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TradeResponse(BaseModel):
    """Response schema for a single trade."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    signal_id: int
    entry_price: float
    exit_price: float | None
    quantity: float
    pnl: float | None
    status: str
    opened_at: datetime
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TradeStatsResponse(BaseModel):
    """Aggregated performance statistics for paper trading."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    total_pnl_percent: float
    avg_win: float
    avg_loss: float
    best_trade: float
    worst_trade: float
    max_drawdown: float
    sharpe_ratio: float | None
    current_balance: float
    open_trades: int
