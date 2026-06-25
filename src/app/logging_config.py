"""Structured logging setup.

Uses loguru for one-line setup. JSON-serialized output to stdout so the log
stream is friendly to cloud log aggregators (Cloudwatch, Stackdriver, Loki).

Privacy: we never log raw message bodies. Only a SHA-256 prefix and length are
recorded in request logs.
"""

from __future__ import annotations

import sys

from loguru import logger

from app.config import get_settings


def setup_logging() -> None:
    """Configure loguru. Idempotent — safe to call multiple times."""
    settings = get_settings()

    # Remove the default stderr handler
    logger.remove()

    # Add a JSON sink on stdout. `serialize=True` emits JSON; `enqueue=True`
    # makes logging safe across worker processes/threads.
    logger.add(
        sys.stdout,
        level=settings.log_level.upper(),
        serialize=True,
        enqueue=True,
        backtrace=False,
        diagnose=False,
        format="{message}",
    )

    logger.info(
        "logging_configured",
        app=settings.app_name,
        env=settings.app_env,
        level=settings.log_level,
    )


def get_logger():
    """Return the configured logger."""
    return logger