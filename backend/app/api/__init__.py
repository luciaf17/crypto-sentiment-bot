from app.api.backtest import router as backtest_router
from app.api.health import router as health_router
from app.api.prices import router as prices_router
from app.api.signals import router as signals_router
from app.api.trades import router as trades_router

__all__ = [
    "backtest_router",
    "health_router",
    "prices_router",
    "signals_router",
    "trades_router",
]
