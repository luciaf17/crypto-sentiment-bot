import logging

import requests

logger = logging.getLogger(__name__)


class FearGreedIndex:
    """Fetches the Crypto Fear & Greed Index from alternative.me."""

    BASE_URL = "https://api.alternative.me/fng/"

    def get_current(self) -> dict:
        """Fetch the current Fear & Greed Index value.

        Returns:
            Dict with value (0-100), classification, timestamp,
            and normalized_score (-1 to 1). Returns defaults on error.
        """
        try:
            response = requests.get(
                self.BASE_URL, params={"limit": "1"}, timeout=15
            )
            response.raise_for_status()
            data = response.json()

            entries = data.get("data", [])
            if not entries:
                logger.warning("Fear & Greed Index returned no data")
                return self._default_result()

            entry = entries[0]
            value = int(entry.get("value", 50))
            classification = entry.get("value_classification", "Neutral")
            timestamp = entry.get("timestamp", "")

            # Map 0-100 to -1 to 1: (value - 50) / 50
            normalized_score = (value - 50) / 50.0

            logger.info(
                "Fear & Greed Index: %d (%s), normalized=%.2f",
                value,
                classification,
                normalized_score,
            )

            return {
                "value": value,
                "classification": classification,
                "timestamp": timestamp,
                "normalized_score": normalized_score,
            }

        except requests.exceptions.RequestException as e:
            logger.error("Failed to fetch Fear & Greed Index: %s", e)
            return self._default_result()

    @staticmethod
    def _default_result() -> dict:
        """Return a neutral default when the API is unavailable."""
        return {
            "value": 50,
            "classification": "Neutral",
            "timestamp": "",
            "normalized_score": 0.0,
        }
