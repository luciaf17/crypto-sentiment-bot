from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "crypto_bot",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule={
        "collect-btc-price-every-5-minutes": {
            "task": "app.tasks.price_tasks.collect_btc_price",
            "schedule": 300.0,  # 5 minutes in seconds
        },
    },
)

# IMPORTANTE: Importar las tasks EXPLÍCITAMENTE
from app.tasks import price_tasks  # noqa: E402, F401