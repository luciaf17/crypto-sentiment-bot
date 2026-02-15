"""Database model for persisting backtest results.

Stores the configuration, metrics, and trade history of each backtest run
so they can be retrieved later for comparison and analysis.
"""

import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BacktestRun(Base):
    """Persisted record of a single backtest execution."""

    __tablename__ = "backtest_runs"

    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    trades: Mapped[list] = mapped_column(JSON, nullable=False)
    equity_curve: Mapped[list] = mapped_column(JSON, nullable=False)
    data_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="completed"
    )
    error_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
