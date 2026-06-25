"""Shared pytest fixtures.

We build an isolated FastAPI app instance per test (via the factory function)
and wrap it in an httpx AsyncClient using ASGITransport. This means tests run
in-process with no listening port — fast and deterministic.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import create_app


@pytest.fixture
def app():
    """Return a fresh FastAPI application instance."""
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    """Return an httpx AsyncClient bound to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac