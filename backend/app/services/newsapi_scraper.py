import logging
import time

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class NewsAPIScraper:
    """Fetches crypto news from NewsAPI."""

    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self) -> None:
        self.api_key = settings.newsapi_key

    def get_crypto_news(
        self, query: str = "bitcoin OR btc", limit: int = 20
    ) -> list[dict]:
        """Fetch recent news articles matching a query.

        Args:
            query: Search query string.
            limit: Maximum number of articles to return.

        Returns:
            List of dicts with title, description, source,
            published_at, and url.
        """
        if not self.api_key:
            logger.warning("NewsAPI key not configured, skipping")
            return []

        params = {
            "q": query,
            "apiKey": self.api_key,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": limit,
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(
                    self.BASE_URL, params=params, timeout=15
                )

                if response.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    logger.warning(
                        "NewsAPI rate limited (attempt %d/%d). "
                        "Retrying in %ds...",
                        attempt + 1,
                        max_retries,
                        wait,
                    )
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                data = response.json()

                if data.get("status") != "ok":
                    logger.error(
                        "NewsAPI returned error: %s",
                        data.get("message", "unknown"),
                    )
                    return []

                results: list[dict] = []
                for article in data.get("articles", [])[:limit]:
                    results.append(
                        {
                            "title": article.get("title", ""),
                            "description": article.get("description", ""),
                            "source": article.get("source", {}).get(
                                "name", "unknown"
                            ),
                            "published_at": article.get("publishedAt", ""),
                            "url": article.get("url", ""),
                        }
                    )

                logger.info(
                    "Fetched %d articles from NewsAPI for query=%r",
                    len(results),
                    query,
                )
                return results

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    logger.warning(
                        "NewsAPI request failed (attempt %d/%d): %s. "
                        "Retrying in %ds...",
                        attempt + 1,
                        max_retries,
                        e,
                        wait,
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        "NewsAPI request failed after %d attempts: %s",
                        max_retries,
                        e,
                    )

        return []
