"""Confidence scoring tests."""

from __future__ import annotations

import pytest

from app.confidence import MatchSignals, compute_confidence
from app.schemas import CaseType, Severity


def test_other_default_confidence_is_low():
    c = compute_confidence(CaseType.OTHER, MatchSignals(), Severity.LOW)
    assert c == 0.30


def test_any_pattern_hit_floors_at_065():
    c = compute_confidence(
        CaseType.PHISHING_OR_SOCIAL_ENGINEERING,
        MatchSignals(phishing_pattern_hits=1),
        Severity.MEDIUM,
    )
    assert c >= 0.65


def test_multiple_patterns_plus_keyword_floors_at_085():
    c = compute_confidence(
        CaseType.PHISHING_OR_SOCIAL_ENGINEERING,
        MatchSignals(phishing_pattern_hits=2, phishing_keyword_hits=1),
        Severity.MEDIUM,
    )
    assert c >= 0.85


def test_critical_severity_adds_bonus():
    base = compute_confidence(
        CaseType.PHISHING_OR_SOCIAL_ENGINEERING,
        MatchSignals(phishing_pattern_hits=1),
        Severity.MEDIUM,
    )
    crit = compute_confidence(
        CaseType.PHISHING_OR_SOCIAL_ENGINEERING,
        MatchSignals(phishing_pattern_hits=1),
        Severity.CRITICAL,
    )
    assert crit >= base


def test_confidence_always_in_0_to_1():
    cases = [
        (CaseType.PAYMENT_FAILED, MatchSignals(payment_pattern_hits=10, payment_keyword_hits=20), Severity.CRITICAL),
        (CaseType.OTHER, MatchSignals(), Severity.LOW),
        (CaseType.PHISHING_OR_SOCIAL_ENGINEERING, MatchSignals(phishing_pattern_hits=3, phishing_keyword_hits=4), Severity.CRITICAL),
        (CaseType.REFUND_REQUEST, MatchSignals(refund_keyword_hits=1), Severity.MEDIUM),
    ]
    for ct, sig, sev in cases:
        c = compute_confidence(ct, sig, sev)
        assert 0.0 <= c <= 1.0


@pytest.mark.asyncio
async def test_e2e_confidence_in_range(client):
    response = await client.post(
        "/sort-ticket",
        json={"ticket_id": "T-C1", "message": "I got a phishing email."},
    )
    conf = response.json()["confidence"]
    assert 0.0 <= conf <= 1.0