"""FastAPI application factory.

Run locally:
    uvicorn app.main:app --reload --port 8000

Run from `src/` so the package import `app` resolves (see Dockerfile and Procfile).
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

from app import __version__
from app.api.health import router as health_router
from app.api.sort_ticket import router as sort_ticket_router
from app.config import get_settings
from app.logging_config import get_logger, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Process startup/shutdown. Records start time for /health uptime."""
    setup_logging()
    log = get_logger()
    settings = get_settings()

    app.state.start_time = time.time()
    log.info(
        "service_started",
        app=settings.app_name,
        version=settings.app_version,
        env=settings.app_env,
        python_version=__version__,
    )

    yield

    log.info("service_stopped", app=settings.app_name)


def create_app() -> FastAPI:
    """Build and return the FastAPI application.

    Kept as a factory function (rather than a module-level `app = FastAPI()`)
    so tests can build isolated instances and override dependencies.
    """
    settings = get_settings()

    app = FastAPI(
        title="QueueStorm Warmup — CRM Ticket Classifier",
        description=(
            "Rule-based classifier for inbound CRM support tickets. "
            "Routes to customer_support, dispute_resolution, payments_ops, "
            "or fraud_risk based on the detected case type and severity."
        ),
        version=settings.app_version,
        lifespan=lifespan,
    )

    # Routers
    app.include_router(health_router)
    app.include_router(sort_ticket_router)

    # Uniform error shape for validation errors
    @app.exception_handler(RequestValidationError)
    async def _validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "detail": "Request validation failed.",
                "error_code": "VALIDATION_ERROR",
                "errors": exc.errors(),
            },
        )

    return app


# Module-level app for `uvicorn app.main:app`
app = create_app()