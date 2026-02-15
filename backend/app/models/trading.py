import datetime
import enum

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SignalAction(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class TradeStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (
        Index("ix_price_history_symbol", "symbol"),
        Index("ix_price_history_timestamp", "timestamp"),
        Index("ix_price_history_symbol_timestamp", "symbol", "timestamp"),
    )

    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)

    def __repr__(self) -> str:
        return f"<PriceHistory(symbol={self.symbol!r}, price={self.price}, timestamp={self.timestamp})>"


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"
    __table_args__ = (
        Index("ix_sentiment_scores_symbol", "symbol"),
        Index("ix_sentiment_scores_timestamp", "timestamp"),
        Index("ix_sentiment_scores_symbol_timestamp", "symbol", "timestamp"),
    )

    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    def __repr__(self) -> str:
        return f"<SentimentScore(symbol={self.symbol!r}, score={self.score}, source={self.source!r})>"


class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = (
        Index("ix_signals_symbol", "symbol"),
        Index("ix_signals_timestamp", "timestamp"),
    )

    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[SignalAction] = mapped_column(
        Enum(SignalAction), nullable=False
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    price_at_signal: Mapped[float] = mapped_column(Float, nullable=False)
    reasons: Mapped[dict] = mapped_column(JSON, nullable=False)
    technical_indicators: Mapped[dict] = mapped_column(JSON, nullable=False)
    sentiment_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    trades: Mapped[list["Trade"]] = relationship("Trade", back_populates="signal")

    def __repr__(self) -> str:
        return f"<Signal(symbol={self.symbol!r}, action={self.action.value}, confidence={self.confidence})>"


class Trade(Base):
    __tablename__ = "trades"

    signal_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("signals.id"), nullable=False
    )
    entry_price: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[TradeStatus] = mapped_column(
        Enum(TradeStatus), nullable=False, default=TradeStatus.OPEN
    )
    opened_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    closed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    signal: Mapped["Signal"] = relationship("Signal", back_populates="trades")

    def __repr__(self) -> str:
        return f"<Trade(signal_id={self.signal_id}, status={self.status.value}, pnl={self.pnl})>"
