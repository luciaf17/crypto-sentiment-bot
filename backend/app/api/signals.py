"""API endpoints for trading signals."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.trading import Signal, SignalAction
from app.schemas.signal import SignalResponse, SignalStatsResponse

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/latest", response_model=list[SignalResponse])
def get_latest_signals(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db_session),
) -> list[Signal]:
    """Return the most recent trading signals.

    Ordered by timestamp descending (newest first).
    """
    signals = (
        db.query(Signal)
        .order_by(desc(Signal.timestamp))
        .limit(limit)
        .all()
    )
    return signals


@router.get("/current", response_model=SignalResponse)
def get_current_signal(
    symbol: str = Query(default="BTC/USDT"),
    db: Session = Depends(get_db_session),
) -> Signal:
    """Return the most recent signal for a given symbol."""
    signal = (
        db.query(Signal)
        .filter(Signal.symbol == symbol)
        .order_by(desc(Signal.timestamp))
        .first()
    )

    if not signal:
        raise HTTPException(
            status_code=404,
            detail=f"No signals found for symbol '{symbol}'",
        )

    return signal


@router.get("/stats", response_model=SignalStatsResponse)
def get_signal_stats(
    db: Session = Depends(get_db_session),
) -> SignalStatsResponse:
    """Return aggregated statistics about all generated signals.

    Includes signal distribution (BUY/SELL/HOLD counts and percentages)
    and average confidence across all signals.
    """
    total = db.query(func.count(Signal.id)).scalar() or 0

    if total == 0:
        return SignalStatsResponse(
            total_signals=0,
            buy_count=0,
            sell_count=0,
            hold_count=0,
            buy_pct=0.0,
            sell_pct=0.0,
            hold_pct=0.0,
            avg_confidence=0.0,
            latest_signal_at=None,
        )

    buy_count = (
        db.query(func.count(Signal.id))
        .filter(Signal.action == SignalAction.BUY)
        .scalar() or 0
    )
    sell_count = (
        db.query(func.count(Signal.id))
        .filter(Signal.action == SignalAction.SELL)
        .scalar() or 0
    )
    hold_count = (
        db.query(func.count(Signal.id))
        .filter(Signal.action == SignalAction.HOLD)
        .scalar() or 0
    )

    avg_confidence = db.query(func.avg(Signal.confidence)).scalar() or 0.0

    latest_signal_at = db.query(func.max(Signal.timestamp)).scalar()

    return SignalStatsResponse(
        total_signals=total,
        buy_count=buy_count,
        sell_count=sell_count,
        hold_count=hold_count,
        buy_pct=round(buy_count / total * 100, 1),
        sell_pct=round(sell_count / total * 100, 1),
        hold_pct=round(hold_count / total * 100, 1),
        avg_confidence=round(float(avg_confidence), 4),
        latest_signal_at=latest_signal_at,
    )
