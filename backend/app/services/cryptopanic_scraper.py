import logging
import time

import requests

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class CryptoPanicScraper:
    """Fetches crypto news and sentiment from CryptoPanic API."""

    BASE_URL = "https://cryptopanic.com/api/developer/v2/posts/"

    def __init__(self) -> None:
        self.api_key = settings.cryptopanic_api_key

    def get_news(
        self, currencies: str = "BTC", limit: int = 20
    ) -> list[dict]:
        """Fetch recent news posts for given currencies.

        Args:
            currencies: Comma-separated currency codes (e.g. "BTC,ETH").
            limit: Maximum number of posts to return.

        Returns:
            List of dicts with title, published_at, source_name, url,
            votes, and sentiment_score.
        """
        if not self.api_key:
            logger.warning("CryptoPanic API key not configured, skipping")
            return []

        params = {
        "auth_token": self.api_key,
        "currencies": currencies,
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
                        "CryptoPanic rate limited (attempt %d/%d). "
                        "Retrying in %ds...",
                        attempt + 1,
                        max_retries,
                        wait,
                    )
                    time.sleep(wait)
                    continue

                response.raise_for_status()
                data = response.json()

                results: list[dict] = []
                for post in data.get("results", [])[:limit]:
                    votes = post.get("votes", {})
                    positive = votes.get("positive", 0)
                    negative = votes.get("negative", 0)
                    total = positive + negative + votes.get("important", 0) + votes.get("liked", 0) + votes.get("disliked", 0) + votes.get("lol", 0) + votes.get("toxic", 0) + votes.get("saved", 0) + votes.get("comments", 0)

                    if total > 0:
                        sentiment_score = max(
                            -1.0,
                            min(1.0, (positive - negative) / total),
                        )
                    else:
                        sentiment_score = 0.0

                    results.append(
                        {
                            "title": post.get("title", ""),
                            "published_at": post.get("published_at", ""),
                            "source_name": post.get("source", {}).get(
                                "title", "unknown"
                            ),
                            "url": post.get("url", ""),
                            "votes": {
                                "positive": positive,
                                "negative": negative,
                                "total": total,
                            },
                            "sentiment_score": sentiment_score,
                        }
                    )

                logger.info(
                    "Fetched %d posts from CryptoPanic for %s",
                    len(results),
                    currencies,
                )
                return results

            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    wait = 2 ** (attempt + 1)
                    logger.warning(
                        "CryptoPanic request failed (attempt %d/%d): %s. "
                        "Retrying in %ds...",
                        attempt + 1,
                        max_retries,
                        e,
                        wait,
                    )
                    time.sleep(wait)
                else:
                    logger.error(
                        "CryptoPanic request failed after %d attempts: %s",
                        max_retries,
                        e,
                    )

        return []
