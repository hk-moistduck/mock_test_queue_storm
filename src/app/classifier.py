"""Classifier orchestrator.

The single entry point for processing a ticket end-to-end:

    raw message -> normalize
                -> classify_case_type  (returns (case_type, signals))
                -> assign_severity
                -> route_to_department
                -> build_summary
                -> sanitize_summary (safety)
                -> compute_confidence
                -> mark human_review_required
                -> SortTicketResponse

Kept as a pure function over the request payload so it's trivially testable.
"""

from __future__ import annotations

import re
import unicodedata

from app.confidence import MatchSignals, compute_confidence
from app.rules import (
    PAYMENT_FAILED_KEYWORDS,
    PAYMENT_FAILED_PATTERNS,
    PHISHING_KEYWORDS,
    PHISHING_PATTERNS,
    REFUND_REQUEST_KEYWORDS,
    REFUND_REQUEST_PATTERNS,
    WRONG_TRANSFER_KEYWORDS,
    WRONG_TRANSFER_PATTERNS,
)
from app.safety import sanitize_summary
from app.schemas import (
    CaseType,
    Department,
    Severity,
    SortTicketRequest,
    SortTicketResponse,
)
from app.severity import assign_severity
from app.summarizer import build_summary

#: Routing table — pure lookup, no logic.
ROUTING: dict[CaseType, Department] = {
    CaseType.PHISHING_OR_SOCIAL_ENGINEERING: Department.FRAUD_RISK,
    CaseType.WRONG_TRANSFER: Department.DISPUTE_RESOLUTION,
    CaseType.REFUND_REQUEST: Department.DISPUTE_RESOLUTION,
    CaseType.PAYMENT_FAILED: Department.PAYMENTS_OPS,
    CaseType.OTHER: Department.CUSTOMER_SUPPORT,
}


def _normalize(message: str) -> str:
    """NFKC-normalize and lowercase for matching. Original casing is preserved
    in the request payload for echoing."""
    return unicodedata.normalize("NFKC", message).lower()


def _count_keyword_hits(message_lower: str, keywords: frozenset[str]) -> int:
    """Count how many distinct keywords appear in the message."""
    return sum(1 for kw in keywords if kw in message_lower)


def _count_pattern_hits(message: str, patterns: tuple[re.Pattern[str], ...]) -> int:
    """Count how many patterns match the message."""
    return sum(1 for p in patterns if p.search(message))


def classify_case_type(message_lower: str) -> tuple[CaseType, MatchSignals]:
    """Return (case_type, signals) using ordered, first-match-wins rules."""
    # 1. Phishing (most dangerous)
    p_hits = _count_pattern_hits(message_lower, PHISHING_PATTERNS)
    k_hits = _count_keyword_hits(message_lower, PHISHING_KEYWORDS)
    if p_hits or k_hits:
        return CaseType.PHISHING_OR_SOCIAL_ENGINEERING, MatchSignals(
            phishing_pattern_hits=p_hits,
            phishing_keyword_hits=k_hits,
        )

    # 2. Wrong transfer
    p_hits = _count_pattern_hits(message_lower, WRONG_TRANSFER_PATTERNS)
    k_hits = _count_keyword_hits(message_lower, WRONG_TRANSFER_KEYWORDS)
    if p_hits or k_hits:
        return CaseType.WRONG_TRANSFER, MatchSignals(
            wrong_xfer_pattern_hits=p_hits,
            wrong_xfer_keyword_hits=k_hits,
        )

    # 3. Refund request
    p_hits = _count_pattern_hits(message_lower, REFUND_REQUEST_PATTERNS)
    k_hits = _count_keyword_hits(message_lower, REFUND_REQUEST_KEYWORDS)
    if p_hits or k_hits:
        return CaseType.REFUND_REQUEST, MatchSignals(
            refund_pattern_hits=p_hits,
            refund_keyword_hits=k_hits,
        )

    # 4. Payment failed
    p_hits = _count_pattern_hits(message_lower, PAYMENT_FAILED_PATTERNS)
    k_hits = _count_keyword_hits(message_lower, PAYMENT_FAILED_KEYWORDS)
    if p_hits or k_hits:
        return CaseType.PAYMENT_FAILED, MatchSignals(
            payment_pattern_hits=p_hits,
            payment_keyword_hits=k_hits,
        )

    # 5. Default
    return CaseType.OTHER, MatchSignals()


def process_ticket(payload: SortTicketRequest) -> SortTicketResponse:
    """Run the full pipeline. Pure function. No I/O. No logging side-effects."""
    message_lower = _normalize(payload.message)

    # Classify
    case_type, signals = classify_case_type(message_lower)

    # Severity
    severity = assign_severity(case_type, message_lower)

    # Department (pure routing table)
    department = ROUTING[case_type]

    # Build the summary
    summary = build_summary(
        message=payload.message,
        case_type=case_type,
        severity=severity,
        channel=payload.channel,
    )

    # Safety last
    summary = sanitize_summary(summary)

    # Confidence
    confidence = compute_confidence(case_type, signals, severity)

    # Human review flag
    human_review_required = (
        case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING
        or severity == Severity.CRITICAL
    )

    return SortTicketResponse(
        ticket_id=payload.ticket_id,
        case_type=case_type,
        severity=severity,
        department=department,
        agent_summary=summary,
        human_review_required=human_review_required,
        confidence=confidence,
    )