"""Strategy management and configuration."""

import logging
from datetime import datetime, timezone

from app.database import SessionLocal
from app.models.strategy import StrategyConfig

logger = logging.getLogger(__name__)


class StrategyManager:
    """Manages trading strategy configurations."""

    DEFAULT_CONSERVATIVE = {
        "rsi_buy": 25,
        "rsi_sell": 75,
        "sentiment_weight": 0.2,
        "sentiment_min": 0.3,
        "min_confidence": 0.7,
        "stop_loss_percent": 2.0,
        "take_profit_percent": 8.0,
    }

    DEFAULT_BALANCED = {
        "rsi_buy": 35,
        "rsi_sell": 65,
        "sentiment_weight": 0.4,
        "sentiment_min": 0.0,
        "min_confidence": 0.5,
        "stop_loss_percent": 3.0,
        "take_profit_percent": 5.0,
    }

    DEFAULT_AGGRESSIVE = {
        "rsi_buy": 45,
        "rsi_sell": 55,
        "sentiment_weight": 0.6,
        "sentiment_min": -0.2,
        "min_confidence": 0.3,
        "stop_loss_percent": 5.0,
        "take_profit_percent": 3.0,
    }

    @staticmethod
    def calculate_params_from_aggressiveness(
        aggressiveness: int,
    ) -> dict:
        """
        Calculate strategy parameters based on aggressiveness (0-100).

        Args:
            aggressiveness: 0=ultra conservative, 100=ultra aggressive

        Returns:
            Dictionary of strategy parameters
        """
        # Ensure bounds
        agg = max(0, min(100, aggressiveness))

        # Linear interpolation between conservative and aggressive
        params = {
            # RSI: Conservative=25, Aggressive=45
            "rsi_buy": 25 + (agg * 0.2),
            # RSI Sell: Conservative=75, Aggressive=55
            "rsi_sell": 75 - (agg * 0.2),
            # Sentiment weight: Conservative=20%, Aggressive=60%
            "sentiment_weight": 0.2 + (agg * 0.004),
            # Min sentiment: Conservative=0.3, Aggressive=-0.2
            "sentiment_min": 0.3 - (agg * 0.005),
            # Min confidence: Conservative=0.7, Aggressive=0.3
            "min_confidence": 0.7 - (agg * 0.004),
            # Stop loss: Conservative=2%, Aggressive=5%
            "stop_loss_percent": 2.0 + (agg * 0.03),
            # Take profit: Conservative=8%, Aggressive=3%
            "take_profit_percent": 8.0 - (agg * 0.05),
        }

        return params

    @staticmethod
    def get_active_strategy() -> StrategyConfig | None:
        """Get the currently active strategy."""
        db = SessionLocal()
        try:
            return (
                db.query(StrategyConfig)
                .filter(StrategyConfig.is_active == True)
                .first()
            )
        finally:
            db.close()

    @staticmethod
    def get_active_params() -> dict:
        """Get parameters of active strategy, or default balanced."""
        strategy = StrategyManager.get_active_strategy()
        if strategy:
            return strategy.parameters
        return StrategyManager.DEFAULT_BALANCED

    @staticmethod
    def create_strategy(
        name: str,
        aggressiveness: int,
        description: str | None = None,
        created_by: str = "user",
    ) -> StrategyConfig:
        """Create a new strategy configuration."""
        params = StrategyManager.calculate_params_from_aggressiveness(
            aggressiveness
        )

        db = SessionLocal()
        try:
            strategy = StrategyConfig(
                name=name,
                aggressiveness=aggressiveness,
                parameters=params,
                is_active=False,
                description=description,
                created_by=created_by,
            )
            db.add(strategy)
            db.commit()
            db.refresh(strategy)
            logger.info(
                f"Created strategy '{name}' with aggressiveness {aggressiveness}"
            )
            return strategy
        finally:
            db.close()

    @staticmethod
    def activate_strategy(strategy_id: int) -> StrategyConfig:
        """Activate a strategy (deactivates all others)."""
        db = SessionLocal()
        try:
            # Deactivate all
            db.query(StrategyConfig).update(
                {"is_active": False, "activated_at": None}
            )

            # Activate target
            strategy = db.query(StrategyConfig).get(strategy_id)
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")

            strategy.is_active = True
            strategy.activated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(strategy)

            logger.info(
                f"Activated strategy '{strategy.name}' (aggressiveness={strategy.aggressiveness})"
            )
            return strategy
        finally:
            db.close()

    @staticmethod
    def list_strategies(limit: int = 20) -> list[StrategyConfig]:
        """List all strategies, most recent first."""
        db = SessionLocal()
        try:
            return (
                db.query(StrategyConfig)
                .order_by(StrategyConfig.created_at.desc())
                .limit(limit)
                .all()
            )
        finally:
            db.close()