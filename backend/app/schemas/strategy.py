"""Pydantic schemas for strategy configuration."""

from datetime import datetime

from pydantic import BaseModel, Field


class StrategyParameters(BaseModel):
    """Strategy parameters."""

    rsi_buy: float
    rsi_sell: float
    sentiment_weight: float
    sentiment_min: float
    min_confidence: float
    stop_loss_percent: float
    take_profit_percent: float


class StrategyCreateRequest(BaseModel):
    """Request to create a new strategy."""

    name: str = Field(..., min_length=1, max_length=100)
    aggressiveness: int = Field(..., ge=0, le=100)
    description: str | None = None


class StrategyResponse(BaseModel):
    """Strategy configuration response."""

    id: int
    name: str
    aggressiveness: int
    parameters: StrategyParameters
    is_active: bool
    description: str | None
    created_by: str | None
    created_at: datetime
    activated_at: datetime | None

    class Config:
        from_attributes = True


class StrategyActivateRequest(BaseModel):
    """Request to activate a strategy."""

    strategy_id: int


class StrategyPreviewRequest(BaseModel):
    """Request to preview strategy parameters."""

    aggressiveness: int = Field(..., ge=0, le=100)


class StrategyPreviewResponse(BaseModel):
    """Preview of strategy parameters."""

    aggressiveness: int
    parameters: StrategyParameters
    estimated_trades_per_day: float
    estimated_win_rate: float
    risk_level: str