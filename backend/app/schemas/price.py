from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PriceResponse(BaseModel):
    """Response schema for a single price record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    high: float
    low: float
    open: float
    close: float
    created_at: datetime


class ChartDataPoint(BaseModel):
    """A single OHLCV data point for charting."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class ChartDataResponse(BaseModel):
    """Response schema for chart data."""

    symbol: str
    hours: int
    data: list[ChartDataPoint]
    count: int


class CurrentPriceResponse(BaseModel):
    """Response schema for the current price of a symbol."""

    symbol: str
    price: float
    high: float
    low: float
    open: float
    close: float
    volume: float
    timestamp: datetime


class HealthResponse(BaseModel):
    """Response schema for basic health check."""

    status: str
    version: str


class ServiceStatus(BaseModel):
    """Status of an individual service."""

    status: str
    detail: str | None = None


class SystemHealthResponse(BaseModel):
    """Response schema for detailed system health check."""

    status: str
    version: str
    uptime_seconds: float
    services: dict[str, ServiceStatus]
