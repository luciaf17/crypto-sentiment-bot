"""Pydantic schemas for the backtesting API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class BacktestRequest(BaseModel):
    """Input parameters for launching a backtest run."""

    symbol: str = Field(default="BTC/USDT", description="Trading pair symbol")
    start_date: datetime | None = Field(
        default=None,
        description="Backtest period start (default: 30 days ago)",
    )
    end_date: datetime | None = Field(
        default=None,
        description="Backtest period end (default: now)",
    )
    strategy_params: dict | None = Field(
        default=None,
        description=(
            "Optional overrides for strategy parameters: "
            "rsi_oversold, rsi_overbought, position_size, "
            "stop_loss_percent, take_profit_percent, initial_balance"
        ),
    )


# ---------------------------------------------------------------------------
# Sub-schemas used in responses
# ---------------------------------------------------------------------------

class BacktestTradeSchema(BaseModel):
    """A single simulated trade produced during the backtest."""

    entry_price: float
    entry_time: str
    exit_price: float | None = None
    exit_time: str | None = None
    quantity: float
    pnl: float | None = None
    pnl_percent: float | None = None
    exit_reason: str | None = None
    rsi: float | None = None
    sentiment: float | None = None


class BacktestMetrics(BaseModel):
    """Aggregate performance statistics for a backtest run."""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float | None = None
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    sharpe_ratio: float | None = None
    best_trade: float = 0.0
    worst_trade: float = 0.0
    avg_hold_duration_hours: float | None = None
    final_balance: float = 0.0


class EquityCurvePoint(BaseModel):
    """A single point on the equity curve."""

    timestamp: str
    balance: float


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class BacktestResponse(BaseModel):
    """Full response for a completed (or failed) backtest run."""

    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    status: str
    symbol: str
    period_start: str | None = None
    period_end: str | None = None
    data_points: int = 0
    parameters: dict
    metrics: BacktestMetrics
    trades: list[BacktestTradeSchema] = []
    equity_curve: list[EquityCurvePoint] = []
    error_reason: str | None = None
    created_at: datetime | None = None


class QuickBacktestRequest(BaseModel):
    """Input for a quick backtest using Strategy Tuner parameters."""

    symbol: str = Field(default="BTC/USDT", description="Trading pair symbol")
    strategy_params: dict = Field(
        ...,
        description="Strategy parameters from the Strategy Tuner preview",
    )
    days: int = Field(
        default=7,
        ge=1,
        le=90,
        description="Number of days to backtest (default: 7)",
    )


class ActiveStrategyComparison(BaseModel):
    """Comparison between the tested strategy and the current active one."""

    active_strategy_name: str
    active_pnl: float
    active_pnl_percent: float
    active_win_rate: float
    active_total_trades: int
    active_sharpe_ratio: float | None = None
    pnl_difference: float
    pnl_percent_difference: float
    win_rate_difference: float
    is_better: bool = Field(
        description="True if the tested strategy outperformed the active one"
    )


class QuickBacktestResponse(BaseModel):
    """Response for the quick backtest endpoint with optional comparison."""

    model_config = ConfigDict(from_attributes=True)

    result: BacktestResponse
    comparison: ActiveStrategyComparison | None = None


class BacktestCompareResponse(BaseModel):
    """Comparison of multiple backtest runs side-by-side."""

    runs: list[BacktestResponse]
    best_by_pnl: int | None = Field(
        default=None, description="ID of the run with the highest total P&L"
    )
    best_by_sharpe: int | None = Field(
        default=None, description="ID of the run with the best Sharpe ratio"
    )
    best_by_drawdown: int | None = Field(
        default=None,
        description="ID of the run with the lowest max drawdown",
    )
