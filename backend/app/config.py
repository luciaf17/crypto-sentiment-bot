from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://crypto_user:crypto_pass@db:5432/crypto_bot"
    
    # Redis
    redis_url: str = "redis://redis:6379/0"
    
    # Binance
    binance_api_key: str = ""
    binance_api_secret: str = ""
    
    # Twitter
    twitter_bearer_token: str = ""
    
    # App
    debug: bool = True
    log_level: str = "INFO"
    
    # Trading
    default_symbol: str = "BTC/USDT"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()