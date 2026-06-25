"""Summarizer tests."""

from __future__ import annotations

import pytest

from app.summarizer import MAX_SUMMARY_CHARS, build_summary
from app.schemas import CaseType, Severity


def test_summary_is_nonempty_and_short():
    s = build_summary(
        message="My payment failed.",
        case_type=CaseType.PAYMENT_FAILED,
        severity=Severity.MEDIUM,
    )
    assert s
    assert len(s) <= MAX_SUMMARY_CHARS


def test_summary_mentions_fraud_risk_for_phishing():
    s = build_summary(
        message="phishing scam",
        case_type=CaseType.PHISHING_OR_SOCIAL_ENGINEERING,
        severity=Severity.CRITICAL,
    )
    assert "fraud_risk" in s.lower()


def test_summary_appends_severity_hint_for_critical():
    s = build_summary(
        message="phishing",
        case_type=CaseType.PHISHING_OR_SOCIAL_ENGINEERING,
        severity=Severity.CRITICAL,
    )
    assert "critical" in s.lower()


def test_summary_never_echoes_raw_message():
    raw = "Hello, this is a very specific and unique ticket message body 12345."
    s = build_summary(raw, CaseType.OTHER, Severity.LOW)
    assert "12345" not in s
    assert "unique ticket message body" not in s.lower()


def test_summary_includes_amount_when_present():
    s = build_summary(
        message="I was charged $49.99 but the payment failed.",
        case_type=CaseType.PAYMENT_FAILED,
        severity=Severity.MEDIUM,
    )
    assert "49.99" in s or "$49.99" in s


@pytest.mark.asyncio
async def test_e2e_summary_under_280_chars(client):
    response = await client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-SUM-1",
            "message": "My payment failed at the grocery store today.",
        },
    )
    s = response.json()["agent_summary"]
    assert len(s) <= 280