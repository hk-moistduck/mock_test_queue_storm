"""Health endpoint tests."""

from __future__ import annotations

import time

import pytest


@pytest.mark.asyncio
async def test_health_returns_200_and_shape(client):
    """GET /health returns 200 with all required fields."""
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["service"] == "queue-storm-warmup"
    assert isinstance(body["version"], str) and body["version"]
    assert isinstance(body["uptime_seconds"], (int, float)) and body["uptime_seconds"] >= 0
    assert isinstance(body["timestamp"], str) and body["timestamp"].endswith("+00:00") or body["timestamp"].endswith("Z")


@pytest.mark.asyncio
async def test_health_under_10s(client):
    """GET /health must respond within the 10-second SLA."""
    started = time.perf_counter()
    response = await client.get("/health")
    elapsed = time.perf_counter() - started
    assert response.status_code == 200
    assert elapsed < 10.0
