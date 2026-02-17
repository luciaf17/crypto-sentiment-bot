"""FastAPI router for backtesting endpoints.

Provides endpoints to run backtests, retrieve saved results, and compare
multiple strategy variations side-by-side.
"""

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.schemas.backtest import (
    ActiveStrategyComparison,
    BacktestCompareResponse,
    BacktestMetrics,
    BacktestRequest,
    BacktestResponse,
    BacktestTradeSchema,
    EquityCurvePoint,
    QuickBacktestRequest,
    QuickBacktestResponse,
)
from app.services.backtester import Backtester
from app.services.strategy_manager import StrategyManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest) -> BacktestResponse:
    """Run a backtest with the given parameters.

    Executes the strategy over historical data and returns full metrics,
    trade list, and equity curve.  The result is also persisted in the
    database so it can be retrieved later via ``GET /results/{id}``.
    """
    backtester = Backtester()

    try:
        result = backtester.run_backtest(
            symbol=request.symbol,
            start_date=request.start_date,
            end_date=request.end_date,
            strategy_params=request.strategy_params,
            save=True,
        )
    except Exception as exc:
        logger.exception("Backtest failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return _result_to_response(result)


@router.post("/quick", response_model=QuickBacktestResponse)
async def quick_backtest(request: QuickBacktestRequest) -> QuickBacktestResponse:
    """Run a quick backtest (default last 7 days) with strategy comparison.

    Designed for the Strategy Tuner: accepts preview parameters, runs the
    backtest, and optionally compares results against the current active
    strategy over the same period.
    """
    backtester = Backtester()
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=request.days)

    try:
        result = backtester.run_backtest(
            symbol=request.symbol,
            start_date=start_date,
            end_date=end_date,
            strategy_params=request.strategy_params,
            save=False,
        )
    except Exception as exc:
        logger.exception("Quick backtest failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    response = _result_to_response(result)

    # Compare against active strategy if one exists
    comparison = None
    active = StrategyManager.get_active_strategy()
    if active is not None:
        try:
            active_result = backtester.run_backtest(
                symbol=request.symbol,
                start_date=start_date,
                end_date=end_date,
                strategy_params=active.parameters,
                save=False,
            )
            active_metrics = active_result.get("metrics", {})
            tested_metrics = result.get("metrics", {})

            comparison = ActiveStrategyComparison(
                active_strategy_name=active.name,
                active_pnl=active_metrics.get("total_pnl", 0.0),
                active_pnl_percent=active_metrics.get("total_pnl_percent", 0.0),
                active_win_rate=active_metrics.get("win_rate", 0.0),
                active_total_trades=active_metrics.get("total_trades", 0),
                active_sharpe_ratio=active_metrics.get("sharpe_ratio"),
                pnl_difference=round(
                    tested_metrics.get("total_pnl", 0.0)
                    - active_metrics.get("total_pnl", 0.0),
                    2,
                ),
                pnl_percent_difference=round(
                    tested_metrics.get("total_pnl_percent", 0.0)
                    - active_metrics.get("total_pnl_percent", 0.0),
                    2,
                ),
                win_rate_difference=round(
                    tested_metrics.get("win_rate", 0.0)
                    - active_metrics.get("win_rate", 0.0),
                    2,
                ),
                is_better=(
                    tested_metrics.get("total_pnl", 0.0)
                    > active_metrics.get("total_pnl", 0.0)
                ),
            )
        except Exception:
            logger.warning(
                "Failed to run comparison backtest for active strategy",
                exc_info=True,
            )

    return QuickBacktestResponse(result=response, comparison=comparison)


@router.get("/results/{backtest_id}", response_model=BacktestResponse)
async def get_backtest_result(backtest_id: int) -> BacktestResponse:
    """Retrieve a previously saved backtest run by its ID."""
    run = Backtester.get_result(backtest_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Backtest run not found")

    return BacktestResponse(
        id=run.id,
        status=run.status,
        symbol=run.symbol,
        period_start=run.start_date.isoformat(),
        period_end=run.end_date.isoformat(),
        data_points=run.data_points,
        parameters=run.parameters,
        metrics=BacktestMetrics(**run.metrics),
        trades=[BacktestTradeSchema(**t) for t in run.trades],
        equity_curve=[EquityCurvePoint(**p) for p in run.equity_curve],
        error_reason=run.error_reason,
        created_at=run.created_at,
    )


@router.get("/compare", response_model=BacktestCompareResponse)
async def compare_backtests(
    ids: str = Query(
        ...,
        description="Comma-separated list of backtest run IDs to compare",
    ),
) -> BacktestCompareResponse:
    """Compare multiple backtest runs side-by-side.

    Pass IDs as a comma-separated string, e.g. ``?ids=1,2,3``.
    Returns all runs along with pointers to the best performing one
    by P&L, Sharpe ratio, and max drawdown.
    """
    try:
        id_list = [int(x.strip()) for x in ids.split(",") if x.strip()]
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="ids must be comma-separated integers"
        ) from exc

    if len(id_list) < 2:
        raise HTTPException(
            status_code=400, detail="Provide at least 2 IDs to compare"
        )

    runs = Backtester.get_results_for_compare(id_list)
    if not runs:
        raise HTTPException(status_code=404, detail="No backtest runs found")

    responses: list[BacktestResponse] = []
    for run in runs:
        responses.append(
            BacktestResponse(
                id=run.id,
                status=run.status,
                symbol=run.symbol,
                period_start=run.start_date.isoformat(),
                period_end=run.end_date.isoformat(),
                data_points=run.data_points,
                parameters=run.parameters,
                metrics=BacktestMetrics(**run.metrics),
                trades=[BacktestTradeSchema(**t) for t in run.trades],
                equity_curve=[EquityCurvePoint(**p) for p in run.equity_curve],
                error_reason=run.error_reason,
                created_at=run.created_at,
            )
        )

    # Determine "best" runs by different criteria
    best_pnl = max(responses, key=lambda r: r.metrics.total_pnl, default=None)
    best_sharpe = max(
        (r for r in responses if r.metrics.sharpe_ratio is not None),
        key=lambda r: r.metrics.sharpe_ratio,  # type: ignore[arg-type]
        default=None,
    )
    best_dd = min(
        responses,
        key=lambda r: r.metrics.max_drawdown,
        default=None,
    )

    return BacktestCompareResponse(
        runs=responses,
        best_by_pnl=best_pnl.id if best_pnl else None,
        best_by_sharpe=best_sharpe.id if best_sharpe else None,
        best_by_drawdown=best_dd.id if best_dd else None,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _result_to_response(result: dict) -> BacktestResponse:
    """Convert the raw dict returned by Backtester into a BacktestResponse."""
    metrics_data = result.get("metrics", {})
    trades_data = result.get("trades", [])
    equity_data = result.get("equity_curve", [])

    return BacktestResponse(
        id=result.get("id"),
        status=result.get("status", "completed"),
        symbol=result.get("symbol", "BTC/USDT"),
        period_start=result.get("period_start"),
        period_end=result.get("period_end"),
        data_points=result.get("data_points", 0),
        parameters=result.get("parameters", {}),
        metrics=BacktestMetrics(**metrics_data),
        trades=[BacktestTradeSchema(**t) for t in trades_data],
        equity_curve=[EquityCurvePoint(**p) for p in equity_data],
        error_reason=result.get("error_reason"),
        created_at=result.get("created_at"),
    )
