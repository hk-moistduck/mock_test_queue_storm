"""Severity assignment tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_phishing_baseline_is_high(client):
    response = await client.post(
        "/sort-ticket",
        json={"ticket_id": "T-S1", "message": "I got a phishing email."},
    )
    assert response.json()["severity"] in {"high", "critical"}


@pytest.mark.asyncio
async def test_phishing_with_urgent_keyword_is_critical(client):
    """A CRITICAL keyword forces severity to critical."""
    response = await client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-S2",
            "message": "I got a phishing email and my account was hacked.",
        },
    )
    body = response.json()
    assert body["case_type"] == "phishing_or_social_engineering"
    assert body["severity"] == "critical"


@pytest.mark.asyncio
async def test_payment_failed_baseline_is_medium(client):
    response = await client.post(
        "/sort-ticket",
        json={"ticket_id": "T-S3", "message": "Payment failed at checkout."},
    )
    body = response.json()
    assert body["case_type"] == "payment_failed"
    assert body["severity"] in {"medium", "high", "critical"}


@pytest.mark.asyncio
async def test_other_baseline_is_low(client):
    response = await client.post(
        "/sort-ticket",
        json={"ticket_id": "T-S4", "message": "What are your business hours?"},
    )
    assert response.json()["severity"] == "low"


@pytest.mark.asyncio
async def test_severity_always_in_enum(client):
    """Severity is always one of the four allowed values."""
    samples = [
        "I need a refund please.",
        "Payment failed.",
        "I got scammed.",
        "Wrong account transfer.",
        "How do I update my profile?",
    ]
    for msg in samples:
        r = await client.post("/sort-ticket", json={"ticket_id": "T-X", "message": msg})
        assert r.status_code == 200
        assert r.json()["severity"] in {"low", "medium", "high", "critical"}
