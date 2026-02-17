"""Strategy configuration model."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StrategyConfig(Base):
    """Stores strategy configuration and history."""

    __tablename__ = "strategy_configs"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    aggressiveness: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # 0-100
    parameters: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(50), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:
        return f"<StrategyConfig(name={self.name!r}, aggressiveness={self.aggressiveness}, active={self.is_active})>"