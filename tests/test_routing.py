"""Routing (department) tests and human_review_required flag tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_phishing_routes_to_fraud_risk(client):
    r = await client.post(
        "/sort-ticket",
        json={"ticket_id": "T-RT-1", "message": "phishing scam asking for my OTP"},
    )
    assert r.json()["department"] == "fraud_risk"


@pytest.mark.asyncio
async def test_refund_request_routes_to_dispute_resolution(client):
    r = await client.post(
        "/sort-ticket",
        json={"ticket_id": "T-RT-2", "message": "Please refund my order."},
    )
    assert r.json()["department"] == "dispute_resolution"


@pytest.mark.asyncio
async def test_wrong_transfer_routes_to_dispute_resolution(client):
    r = await client.post(
        "/sort-ticket",
        json={"ticket_id": "T-RT-3", "message": "I sent money to the wrong account."},
    )
    assert r.json()["department"] == "dispute_resolution"


@pytest.mark.asyncio
async def test_payment_failed_routes_to_payments_ops(client):
    r = await client.post(
        "/sort-ticket",
        json={"ticket_id": "T-RT-4", "message": "Payment failed at checkout."},
    )
    assert r.json()["department"] == "payments_ops"


@pytest.mark.asyncio
async def test_other_routes_to_customer_support(client):
    r = await client.post(
        "/sort-ticket",
        json={"ticket_id": "T-RT-5", "message": "How do I change my password policy?"},
    )
    assert r.json()["department"] == "customer_support"


@pytest.mark.asyncio
async def test_phishing_flags_human_review(client):
    r = await client.post(
        "/sort-ticket",
        json={"ticket_id": "T-RT-6", "message": "I got a phishing email."},
    )
    assert r.json()["human_review_required"] is True


@pytest.mark.asyncio
async def test_critical_severity_flags_human_review(client):
    r = await client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-RT-7",
            "message": "My account was hacked and all my money is gone.",
        },
    )
    body = r.json()
    # Either phishing or critical severity -> human_review_required True
    assert body["human_review_required"] is True


@pytest.mark.asyncio
async def test_low_severity_other_does_not_flag_human_review(client):
    r = await client.post(
        "/sort-ticket",
        json={"ticket_id": "T-RT-8", "message": "What are your business hours?"},
    )
    assert r.json()["human_review_required"] is False