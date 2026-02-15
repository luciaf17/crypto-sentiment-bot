from fastapi import FastAPI
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Crypto Sentiment Trading Bot",
    description="Bot de trading con análisis de sentimiento",
    version="0.1.0",
    debug=settings.debug
)


@app.get("/")
async def root():
    return {
        "message": "Crypto Sentiment Bot API",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}