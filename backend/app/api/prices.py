from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.database import get_db_session
from app.models.trading import PriceHistory
from app.schemas.price import (
    ChartDataPoint,
    ChartDataResponse,
    CurrentPriceResponse,
    PriceResponse,
)

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/latest", response_model=list[PriceResponse])
def get_latest_prices(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db_session),
) -> list[PriceHistory]:
    """Return the latest price records across all symbols."""
    prices = (
        db.query(PriceHistory)
        .order_by(desc(PriceHistory.timestamp))
        .limit(limit)
        .all()
    )
    return prices


@router.get("/chart", response_model=ChartDataResponse)
def get_chart_data(
    symbol: str = Query(default="BTC/USDT"),
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db_session),
) -> ChartDataResponse:
    """Return OHLCV data for charting a given symbol over a time range."""
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    rows = (
        db.query(PriceHistory)
        .filter(
            PriceHistory.symbol == symbol,
            PriceHistory.timestamp >= since,
        )
        .order_by(PriceHistory.timestamp)
        .all()
    )

    data = [
        ChartDataPoint(
            timestamp=row.timestamp,
            open=row.open,
            high=row.high,
            low=row.low,
            close=row.close,
            volume=row.volume,
        )
        for row in rows
    ]

    return ChartDataResponse(
        symbol=symbol,
        hours=hours,
        data=data,
        count=len(data),
    )


@router.get("/current", response_model=CurrentPriceResponse)
def get_current_price(
    symbol: str = Query(default="BTC/USDT"),
    db: Session = Depends(get_db_session),
) -> CurrentPriceResponse:
    """Return the most recent price for a given symbol."""
    latest = (
        db.query(PriceHistory)
        .filter(PriceHistory.symbol == symbol)
        .order_by(desc(PriceHistory.timestamp))
        .first()
    )

    if not latest:
        raise HTTPException(
            status_code=404,
            detail=f"No price data found for symbol '{symbol}'",
        )

    return CurrentPriceResponse(
        symbol=latest.symbol,
        price=latest.price,
        high=latest.high,
        low=latest.low,
        open=latest.open,
        close=latest.close,
        volume=latest.volume,
        timestamp=latest.timestamp,
    )
