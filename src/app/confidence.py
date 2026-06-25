"""Confidence scoring (rule-weighted).

Confidence is computed from the same evidence the classifier used. Stronger
signals (regex pattern hits) carry more weight than keyword hits; severity
adds a small alignment bonus.

This is the inverse of "feeling confident" — it is *quantified* evidence:
how strongly the rules fired, capped and floored to a 0..1 range.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.schemas import CaseType, Severity

#: Per-case weights for pattern hits and keyword hits.
WEIGHTS: dict[CaseType, dict[str, float]] = {
    CaseType.PHISHING_OR_SOCIAL_ENGINEERING: {"pattern": 0.40, "keyword": 0.20},
    CaseType.WRONG_TRANSFER: {"pattern": 0.45, "keyword": 0.20},
    CaseType.REFUND_REQUEST: {"pattern": 0.35, "keyword": 0.20},
    CaseType.PAYMENT_FAILED: {"pattern": 0.30, "keyword": 0.15},
    CaseType.OTHER: {"pattern": 0.0, "keyword": 0.0},
}


@dataclass(frozen=True)
class MatchSignals:
    """How many hits each rule family produced."""

    phishing_pattern_hits: int = 0
    phishing_keyword_hits: int = 0
    wrong_xfer_pattern_hits: int = 0
    wrong_xfer_keyword_hits: int = 0
    refund_pattern_hits: int = 0
    refund_keyword_hits: int = 0
    payment_pattern_hits: int = 0
    payment_keyword_hits: int = 0


def _signals_for(case_type: CaseType, s: MatchSignals) -> tuple[int, int]:
    """Pick the (pattern_hits, keyword_hits) pair for the chosen case_type."""
    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        return s.phishing_pattern_hits, s.phishing_keyword_hits
    if case_type == CaseType.WRONG_TRANSFER:
        return s.wrong_xfer_pattern_hits, s.wrong_xfer_keyword_hits
    if case_type == CaseType.REFUND_REQUEST:
        return s.refund_pattern_hits, s.refund_keyword_hits
    if case_type == CaseType.PAYMENT_FAILED:
        return s.payment_pattern_hits, s.payment_keyword_hits
    return 0, 0  # OTHER


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def compute_confidence(case_type: CaseType, signals: MatchSignals, severity: Severity) -> float:
    """Return a 0..1 confidence score.

    Algorithm:
        raw = clamp(pattern_weight * min(pattern_hits, 3) + keyword_weight * min(keyword_hits, 4), 0, 1)
        if severity == high:     raw += 0.05
        if severity == critical: raw += 0.05
        final = clamp(raw, 0, 1)

        # Floors
        if case_type == OTHER:                          final = max(final, 0.30)
        if pattern_hits >= 1:                           final = max(final, 0.65)
        if pattern_hits >= 2 and keyword_hits >= 1:     final = max(final, 0.85)

        return round(final, 2)
    """
    weights = WEIGHTS[case_type]
    pattern_hits, keyword_hits = _signals_for(case_type, signals)

    raw = weights["pattern"] * min(pattern_hits, 3) + weights["keyword"] * min(keyword_hits, 4)
    raw = _clamp(raw, 0.0, 1.0)

    if severity == Severity.HIGH:
        raw += 0.05
    if severity == Severity.CRITICAL:
        raw += 0.05

    final = _clamp(raw, 0.0, 1.0)

    # Floors
    if case_type == CaseType.OTHER:
        final = max(final, 0.30)
    if pattern_hits >= 1:
        final = max(final, 0.65)
    if pattern_hits >= 2 and keyword_hits >= 1:
        final = max(final, 0.85)

    return round(final, 2)