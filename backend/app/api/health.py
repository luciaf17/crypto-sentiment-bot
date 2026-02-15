import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db_session
from app.schemas.price import (
    HealthResponse,
    ServiceStatus,
    SystemHealthResponse,
)

router = APIRouter(prefix="/health", tags=["health"])

_start_time = time.time()


@router.get("", response_model=HealthResponse)
def health_check() -> HealthResponse:
    """Basic health check endpoint."""
    return HealthResponse(status="healthy", version="0.1.0")


@router.get("/system", response_model=SystemHealthResponse)
def system_health(
    db: Session = Depends(get_db_session),
) -> SystemHealthResponse:
    """Detailed system health check including database and Redis status."""
    settings = get_settings()
    services: dict[str, ServiceStatus] = {}

    # Check database
    try:
        db.execute(text("SELECT 1"))
        services["database"] = ServiceStatus(status="healthy")
    except Exception as e:
        services["database"] = ServiceStatus(status="unhealthy", detail=str(e))

    # Check Redis
    try:
        import redis

        r = redis.from_url(settings.redis_url)
        r.ping()
        services["redis"] = ServiceStatus(status="healthy")
    except Exception as e:
        services["redis"] = ServiceStatus(status="unhealthy", detail=str(e))

    # Check Celery
    try:
        from app.tasks.celery_app import celery_app

        inspect = celery_app.control.inspect(timeout=2.0)
        ping = inspect.ping()
        if ping:
            services["celery"] = ServiceStatus(status="healthy")
        else:
            services["celery"] = ServiceStatus(
                status="unhealthy", detail="No workers responding"
            )
    except Exception as e:
        services["celery"] = ServiceStatus(status="unhealthy", detail=str(e))

    overall = "healthy" if all(
        s.status == "healthy" for s in services.values()
    ) else "degraded"

    return SystemHealthResponse(
        status=overall,
        version="0.1.0",
        uptime_seconds=round(time.time() - _start_time, 2),
        services=services,
    )
