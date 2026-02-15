import asyncio
import logging

from app.config import get_settings
from app.services.price_collector import PriceCollectorService
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)
settings = get_settings()


@celery_app.task(bind=True, name="app.tasks.price_tasks.collect_btc_price")
def collect_btc_price(self) -> dict:
    """Celery task to collect BTC/USDT price and save to database.

    Returns:
        Dictionary with the collected price data.
    """
    symbol = settings.default_symbol
    logger.info("Starting price collection task for %s", symbol)

    try:
        service = PriceCollectorService()

        # Run the async method in a sync context for Celery
        loop = asyncio.new_event_loop()
        try:
            price_data = loop.run_until_complete(
                service.get_current_price(symbol)
            )
        finally:
            loop.close()

        price_record = service.save_price(price_data)

        result = {
            "symbol": symbol,
            "price": price_data["price"],
            "volume": price_data["volume"],
            "record_id": price_record.id,
        }
        logger.info(
            "Price collection task completed: %s = %s",
            symbol,
            price_data["price"],
        )
        return result

    except Exception as e:
        logger.error("Price collection task failed for %s: %s", symbol, e)
        raise self.retry(exc=e, countdown=60, max_retries=3)
