"""GET /health — service health check.

Contract: returns 200 with a small JSON body describing the service status,
version, uptime, and current UTC timestamp. No DB or external calls — should
respond in single-digit milliseconds.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request

from app.config import get_settings
from app.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health(request: Request) -> HealthResponse:
    """Return service status.

    Latency target: <10 seconds (the SLA). Actual: single-digit milliseconds
    because this endpoint performs no I/O.
    """
    settings = get_settings()
    start_time: float = getattr(request.app.state, "start_time", time.time())

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        uptime_seconds=round(time.time() - start_time, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )