"""Schema validation tests for POST /sort-ticket."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_valid_request_returns_200_and_full_response(client):
    """A well-formed request returns 200 with every documented field."""
    payload = {
        "ticket_id": "T-1001",
        "channel": "email",
        "locale": "en-US",
        "message": "My payment failed at checkout, the card was declined.",
    }
    response = await client.post("/sort-ticket", json=payload)
    assert response.status_code == 200
    body = response.json()

    # All required keys present
    required = {
        "ticket_id",
        "case_type",
        "severity",
        "department",
        "agent_summary",
        "human_review_required",
        "confidence",
    }
    assert required.issubset(body.keys())

    # Echoed
    assert body["ticket_id"] == "T-1001"

    # Enum membership
    assert body["case_type"] in {
        "wrong_transfer",
        "payment_failed",
        "refund_request",
        "phishing_or_social_engineering",
        "other",
    }
    assert body["severity"] in {"low", "medium", "high", "critical"}
    assert body["department"] in {
        "customer_support",
        "dispute_resolution",
        "payments_ops",
        "fraud_risk",
    }
    assert isinstance(body["human_review_required"], bool)
    assert isinstance(body["confidence"], (int, float))
    assert 0.0 <= body["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_missing_message_returns_422(client):
    """`message` is required -> 422."""
    response = await client.post("/sort-ticket", json={"ticket_id": "T-1"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_missing_ticket_id_returns_422(client):
    """`ticket_id` is required -> 422."""
    response = await client.post("/sort-ticket", json={"message": "Hello"})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_extra_field_returns_422(client):
    """`extra="forbid"` rejects unknown fields -> 422."""
    response = await client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-1",
            "message": "Hello",
            "unknown_field": "x",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_optional_fields_default_to_none(client):
    """`channel` and `locale` are optional and default to None."""
    response = await client.post(
        "/sort-ticket",
        json={"ticket_id": "T-2", "message": "How do I change my email?"},
    )
    assert response.status_code == 200
    assert response.json()["case_type"] == "other"