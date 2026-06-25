"""Severity assignment.

Algorithm (see README):

1. Start at base severity per case_type.
2. If any CRITICAL_KEYWORD matches -> CRITICAL.
3. Else if any ESCALATE_KEYWORD matches -> bump one tier (low->med->high->critical).
4. Cap at CRITICAL. Never downgrade.
"""

from __future__ import annotations

from app.rules.keywords import CRITICAL_KEYWORDS, ESCALATE_KEYWORDS
from app.schemas import CaseType, Severity

#: Base severity per case_type.
BASE_SEVERITY: dict[CaseType, Severity] = {
    CaseType.PHISHING_OR_SOCIAL_ENGINEERING: Severity.HIGH,
    CaseType.WRONG_TRANSFER: Severity.HIGH,
    CaseType.REFUND_REQUEST: Severity.MEDIUM,
    CaseType.PAYMENT_FAILED: Severity.MEDIUM,
    CaseType.OTHER: Severity.LOW,
}

#: Ordered severity ladder, low -> critical.
_LADDER: list[Severity] = [Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]


def _bump(severity: Severity, levels: int = 1) -> Severity:
    """Move up `levels` steps on the severity ladder, capped at CRITICAL."""
    idx = _LADDER.index(severity)
    new_idx = min(idx + levels, len(_LADDER) - 1)
    return _LADDER[new_idx]


def assign_severity(case_type: CaseType, message_lower: str) -> Severity:
    """Return the severity for a ticket given its case_type and lowercased message.

    `message_lower` must already be lowercased (and ideally NFKC-normalized).
    """
    base = BASE_SEVERITY[case_type]

    # Critical override
    for kw in CRITICAL_KEYWORDS:
        if kw in message_lower:
            return Severity.CRITICAL

    # Escalation
    for kw in ESCALATE_KEYWORDS:
        if kw in message_lower:
            return _bump(base, 1)

    return base