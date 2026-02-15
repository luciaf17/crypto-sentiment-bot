"""Paper trading service for simulated trade execution.

Manages the lifecycle of paper trades: opening positions based on signals,
monitoring stop-loss and take-profit levels, and closing positions with
accurate P&L calculations. Only one position can be open at a time.
"""

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.trading import Signal, SignalAction, Trade, TradeStatus

logger = logging.getLogger(__name__)

# Paper trading configuration
INITIAL_BALANCE = 10000.0  # Starting balance in USD
POSITION_SIZE = 0.1  # BTC per trade
STOP_LOSS_PERCENT = 3.0  # Close if price drops 3% from entry
TAKE_PROFIT_PERCENT = 5.0  # Close if price rises 5% from entry


class PaperTrader:
    """Simulated trader that executes paper trades based on signals.

    Only allows one open trade at a time. Tracks entry/exit prices,
    calculates P&L, and enforces stop-loss / take-profit rules.

    Configuration:
        - initial_balance: 10,000 USD
        - position_size: 0.1 BTC per trade
        - stop_loss: 3% below entry price
        - take_profit: 5% above entry price
    """

    def __init__(
        self,
        session: Session,
        initial_balance: float = INITIAL_BALANCE,
        position_size: float = POSITION_SIZE,
        stop_loss_percent: float = STOP_LOSS_PERCENT,
        take_profit_percent: float = TAKE_PROFIT_PERCENT,
    ) -> None:
        self.session = session
        self.initial_balance = initial_balance
        self.position_size = position_size
        self.stop_loss_percent = stop_loss_percent
        self.take_profit_percent = take_profit_percent

    def get_open_trade(self) -> Trade | None:
        """Return the currently open trade, if any."""
        return (
            self.session.query(Trade)
            .filter(Trade.status == TradeStatus.OPEN)
            .first()
        )

    def check_and_execute_trade(self, signal: Signal) -> Trade | None:
        """Main entry point: decide whether to open or close a trade.

        Logic:
        - If no open trade and signal is BUY → open a long position.
        - If open trade and signal is SELL → close the position.
        - HOLD signals are ignored (no action taken).

        Args:
            signal: The latest trading signal from the signal generator.

        Returns:
            The Trade object if one was opened or closed, None otherwise.
        """
        open_trade = self.get_open_trade()

        if open_trade is None:
            # No open position — only act on BUY signals
            if signal.action == SignalAction.BUY:
                logger.info(
                    "BUY signal received (confidence=%.2f, price=%.2f). "
                    "Opening position.",
                    signal.confidence,
                    signal.price_at_signal,
                )
                return self.open_position(signal)
            else:
                logger.info(
                    "No open trade and signal is %s — no action.",
                    signal.action.value,
                )
                return None
        else:
            # Position is open — only act on SELL signals
            if signal.action == SignalAction.SELL:
                logger.info(
                    "SELL signal received (confidence=%.2f, price=%.2f). "
                    "Closing position.",
                    signal.confidence,
                    signal.price_at_signal,
                )
                return self.close_position(
                    open_trade,
                    exit_price=signal.price_at_signal,
                    exit_reason="SELL signal received",
                )
            else:
                logger.info(
                    "Open trade exists and signal is %s — holding position.",
                    signal.action.value,
                )
                return None

    def open_position(self, signal: Signal) -> Trade:
        """Open a new paper trade based on a BUY signal.

        Creates a Trade record with OPEN status at the signal's price.
        The position size is fixed (default 0.1 BTC).

        Args:
            signal: The BUY signal triggering the trade.

        Returns:
            The newly created Trade object.
        """
        trade = Trade(
            signal_id=signal.id,
            entry_price=signal.price_at_signal,
            quantity=self.position_size,
            status=TradeStatus.OPEN,
            opened_at=datetime.now(timezone.utc),
        )

        self.session.add(trade)
        self.session.commit()
        self.session.refresh(trade)

        logger.info(
            "Opened paper trade id=%d: BUY %.4f BTC @ $%.2f (signal_id=%d)",
            trade.id,
            trade.quantity,
            trade.entry_price,
            signal.id,
        )
        return trade

    def close_position(
        self,
        trade: Trade,
        exit_price: float,
        exit_reason: str,
    ) -> Trade:
        """Close an open trade and calculate P&L.

        P&L formulas:
            pnl_absolute = (exit_price - entry_price) * quantity
            pnl_percent  = ((exit_price - entry_price) / entry_price) * 100

        Args:
            trade: The open Trade to close.
            exit_price: The price at which the position is being closed.
            exit_reason: Human-readable reason (e.g., "SELL signal", "SL hit").

        Returns:
            The updated Trade object with CLOSED status and P&L.
        """
        # Calculate P&L
        pnl = (exit_price - trade.entry_price) * trade.quantity
        pnl_percent = ((exit_price - trade.entry_price) / trade.entry_price) * 100

        trade.exit_price = exit_price
        trade.pnl = round(pnl, 2)
        trade.status = TradeStatus.CLOSED
        trade.closed_at = datetime.now(timezone.utc)

        self.session.commit()
        self.session.refresh(trade)

        logger.info(
            "Closed paper trade id=%d: EXIT @ $%.2f | P&L: $%.2f (%.2f%%) | Reason: %s",
            trade.id,
            exit_price,
            pnl,
            pnl_percent,
            exit_reason,
        )
        return trade

    def check_stop_loss_take_profit(
        self, trade: Trade, current_price: float
    ) -> Trade | None:
        """Check if the current price triggers stop-loss or take-profit.

        Stop-loss: triggers when price drops stop_loss_percent below entry.
        Take-profit: triggers when price rises take_profit_percent above entry.

        Args:
            trade: The open trade to evaluate.
            current_price: The most recent market price.

        Returns:
            The closed Trade if SL/TP was triggered, None otherwise.
        """
        # Calculate SL and TP price levels
        stop_loss_price = trade.entry_price * (1 - self.stop_loss_percent / 100)
        take_profit_price = trade.entry_price * (1 + self.take_profit_percent / 100)

        if current_price <= stop_loss_price:
            # Stop-loss hit — close to limit losses
            logger.warning(
                "STOP-LOSS triggered for trade id=%d: "
                "current=$%.2f <= SL=$%.2f (entry=$%.2f, -%s%%)",
                trade.id,
                current_price,
                stop_loss_price,
                trade.entry_price,
                self.stop_loss_percent,
            )
            return self.close_position(
                trade,
                exit_price=current_price,
                exit_reason=f"Stop-loss hit at ${current_price:.2f} "
                f"(SL level: ${stop_loss_price:.2f})",
            )

        if current_price >= take_profit_price:
            # Take-profit hit — lock in gains
            logger.info(
                "TAKE-PROFIT triggered for trade id=%d: "
                "current=$%.2f >= TP=$%.2f (entry=$%.2f, +%s%%)",
                trade.id,
                current_price,
                take_profit_price,
                trade.entry_price,
                self.take_profit_percent,
            )
            return self.close_position(
                trade,
                exit_price=current_price,
                exit_reason=f"Take-profit hit at ${current_price:.2f} "
                f"(TP level: ${take_profit_price:.2f})",
            )

        # Price is within SL/TP range — no action
        logger.debug(
            "Trade id=%d: price=$%.2f within range [SL=$%.2f, TP=$%.2f]",
            trade.id,
            current_price,
            stop_loss_price,
            take_profit_price,
        )
        return None
