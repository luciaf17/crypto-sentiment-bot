"""Celery tasks for paper trade execution and monitoring.

Runs every 5 minutes to:
1. Check the latest signal and open/close trades accordingly.
2. Monitor open positions for stop-loss / take-profit triggers
   using the most recent market price.
"""

import logging

from sqlalchemy import desc

from app.database import SessionLocal
from app.models.trading import PriceHistory, Signal, TradeStatus, Trade
from app.services.paper_trader import PaperTrader
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="app.tasks.trading_tasks.execute_paper_trades",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    max_retries=3,
)
def execute_paper_trades(self) -> dict:
    """Execute paper trades based on latest signals and check SL/TP.

    This task:
    1. Fetches the most recent trading signal from the database.
    2. Passes it to PaperTrader.check_and_execute_trade() to decide
       whether to open or close a position.
    3. If a trade is already open, checks stop-loss and take-profit
       against the latest market price.

    Retry logic: exponential backoff starting at ~4s, capped at 600s,
    up to 3 retries for any exception.

    Returns:
        Dictionary with execution results for the Celery result backend.
    """
    session = SessionLocal()
    try:
        trader = PaperTrader(session)
        result: dict = {"actions": []}

        # Step 1: Get the latest signal
        latest_signal = (
            session.query(Signal)
            .order_by(desc(Signal.timestamp))
            .first()
        )

        if latest_signal is None:
            logger.warning("No signals found in database — skipping trade execution")
            return {"status": "skipped", "reason": "No signals available"}

        # Step 2: Check if we should open or close a trade based on the signal
        trade = trader.check_and_execute_trade(latest_signal)
        if trade is not None:
            action_type = "opened" if trade.status == TradeStatus.OPEN else "closed"
            result["actions"].append({
                "type": action_type,
                "trade_id": trade.id,
                "entry_price": trade.entry_price,
                "exit_price": trade.exit_price,
                "pnl": trade.pnl,
                "status": trade.status.value,
            })
            logger.info(
                "Trade %s: id=%d, status=%s, pnl=%s",
                action_type, trade.id, trade.status.value, trade.pnl,
            )

        # Step 3: Check SL/TP on any open trade
        open_trade = trader.get_open_trade()
        if open_trade is not None:
            # Get the most recent market price
            latest_price = (
                session.query(PriceHistory)
                .filter(PriceHistory.symbol == "BTC/USDT")
                .order_by(desc(PriceHistory.timestamp))
                .first()
            )

            if latest_price is None:
                logger.warning("No price data available for SL/TP check")
            else:
                sl_tp_result = trader.check_stop_loss_take_profit(
                    open_trade, latest_price.price
                )
                if sl_tp_result is not None:
                    reason = "stop_loss" if sl_tp_result.pnl < 0 else "take_profit"
                    result["actions"].append({
                        "type": reason,
                        "trade_id": sl_tp_result.id,
                        "exit_price": sl_tp_result.exit_price,
                        "pnl": sl_tp_result.pnl,
                        "status": sl_tp_result.status.value,
                    })
                    logger.info(
                        "%s triggered: trade id=%d closed at $%.2f, P&L=$%.2f",
                        reason.upper(),
                        sl_tp_result.id,
                        sl_tp_result.exit_price,
                        sl_tp_result.pnl,
                    )

        result["status"] = "executed"
        result["total_actions"] = len(result["actions"])
        return result

    except Exception as e:
        logger.error("Paper trade execution failed: %s", e)
        raise
    finally:
        session.close()
