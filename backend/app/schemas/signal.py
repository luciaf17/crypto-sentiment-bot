"""Pydantic schemas for signal API responses."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SignalResponse(BaseModel):
    """Response schema for a single trading signal."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    action: str
    confidence: float
    price_at_signal: float
    reasons: dict
    technical_indicators: dict
    sentiment_score: float | None
    timestamp: datetime
    created_at: datetime


class SignalStatsResponse(BaseModel):
    """Aggregated statistics about generated signals."""

    total_signals: int
    buy_count: int
    sell_count: int
    hold_count: int
    buy_pct: float
    sell_pct: float
    hold_pct: float
    avg_confidence: float
    latest_signal_at: datetime | None
