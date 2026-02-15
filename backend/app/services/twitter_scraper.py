import logging
import random
from datetime import datetime, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class TwitterScraper:
    """Scraper for fetching tweets - DEMO MODE with simulated tweets"""

    # Tweets de ejemplo sobre BTC (positivos, negativos, neutrales)
    SAMPLE_TWEETS = [
        "Bitcoin breaking through resistance! This bullish momentum is incredible 🚀📈",
        "BTC looking weak, might dump soon. Not feeling confident about this move",
        "Bitcoin holding steady around 69k. Market seems uncertain right now",
        "Just bought more $BTC! To the moon! 🌙💎",
        "Massive selloff incoming. BTC whales are dumping hard 📉😱",
        "Bitcoin adoption continues to grow. More institutional investors entering",
        "Another day, another BTC consolidation. When will we break out?",
        "This is it! Bitcoin about to explode upward! All signals are bullish!",
        "Concerned about BTC price action. Looks like we're forming a bearish pattern",
        "BTC trading sideways. Volume is low. Waiting for a clear signal",
        "Best time to accumulate Bitcoin! Don't miss this opportunity 🔥",
        "Bitcoin dominance falling. Might be time to rotate into alts",
        "Loving this BTC dip! Adding to my position 💪",
        "Red flags everywhere. BTC could crash to 50k soon",
        "Bitcoin stable at current levels. Good for long-term holders",
        "Bullish divergence on BTC! Technical analysis looking very positive",
        "Fear in the market. Everyone panicking about BTC drop",
        "Bitcoin fundamentals remain strong despite volatility",
        "Selling my BTC. This doesn't look good at all",
        "Neutral on Bitcoin right now. Waiting for more data",
    ]

    def search_tweets(
        self,
        query: str,
        limit: int = 20,
        since_date: Optional[datetime] = None,
    ) -> list[dict]:
        """Search for tweets matching a query (DEMO: returns random samples).

        Args:
            query: Search query string (ignored in demo mode).
            limit: Maximum number of tweets to return.
            since_date: Only return tweets after this date.

        Returns:
            List of dicts with keys: text, created_at, username, url.
        """
        logger.info(
            "🔧 DEMO MODE: Simulating %d tweets for query=%r", limit, query
        )

        tweets = []
        now = datetime.now(timezone.utc)

        for i in range(min(limit, len(self.SAMPLE_TWEETS))):
            # Random tweet from samples
            text = random.choice(self.SAMPLE_TWEETS)

            # Random timestamp in the last 24 hours
            hours_ago = random.uniform(0, 24)
            created_at = now - timedelta(hours=hours_ago)

            tweets.append(
                {
                    "text": text,
                    "created_at": created_at,
                    "username": f"user_{i}",
                    "url": f"https://twitter.com/user_{i}/status/{i}",
                }
            )

        logger.info("✅ Generated %d simulated tweets", len(tweets))
        return tweets