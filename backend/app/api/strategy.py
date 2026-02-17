"""FastAPI router for strategy management."""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.strategy import (
    StrategyActivateRequest,
    StrategyCreateRequest,
    StrategyParameters,
    StrategyPreviewRequest,
    StrategyPreviewResponse,
    StrategyResponse,
)
from app.services.strategy_manager import StrategyManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/strategy", tags=["strategy"])


@router.get("/current", response_model=StrategyResponse)
async def get_current_strategy():
    """Get the currently active strategy."""
    strategy = StrategyManager.get_active_strategy()
    if not strategy:
        raise HTTPException(
            status_code=404, detail="No active strategy found"
        )
    return strategy


@router.get("/list", response_model=list[StrategyResponse])
async def list_strategies(limit: int = 20):
    """List all saved strategies."""
    return StrategyManager.list_strategies(limit=limit)


@router.post("/preview", response_model=StrategyPreviewResponse)
async def preview_strategy(request: StrategyPreviewRequest):
    """Preview what parameters a given aggressiveness would produce."""
    params = StrategyManager.calculate_params_from_aggressiveness(
        request.aggressiveness
    )

    # Estimate metrics based on aggressiveness
    estimated_trades = 0.3 + (request.aggressiveness / 100) * 4.5
    estimated_win_rate = 0.75 - (request.aggressiveness / 100) * 0.2

    if request.aggressiveness < 30:
        risk_level = "Low"
    elif request.aggressiveness < 70:
        risk_level = "Medium"
    else:
        risk_level = "High"

    return StrategyPreviewResponse(
        aggressiveness=request.aggressiveness,
        parameters=StrategyParameters(**params),
        estimated_trades_per_day=round(estimated_trades, 2),
        estimated_win_rate=round(estimated_win_rate, 2),
        risk_level=risk_level,
    )


@router.post("/create", response_model=StrategyResponse)
async def create_strategy(request: StrategyCreateRequest):
    """Create a new strategy configuration."""
    try:
        strategy = StrategyManager.create_strategy(
            name=request.name,
            aggressiveness=request.aggressiveness,
            description=request.description,
        )
        return strategy
    except Exception as e:
        logger.exception("Failed to create strategy")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/activate", response_model=StrategyResponse)
async def activate_strategy(request: StrategyActivateRequest):
    """Activate a strategy (deactivates all others)."""
    try:
        strategy = StrategyManager.activate_strategy(
            request.strategy_id
        )
        return strategy
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.exception("Failed to activate strategy")
        raise HTTPException(status_code=500, detail=str(e)) from e