from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import backtest_router, health_router, prices_router, signals_router, trades_router
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Crypto Sentiment Trading Bot",
    description="Bot de trading con análisis de sentimiento",
    version="0.1.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prices_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(signals_router, prefix="/api")
app.include_router(trades_router, prefix="/api")
app.include_router(backtest_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Crypto Sentiment Bot API",
        "version": "0.1.0",
        "status": "running",
    }
