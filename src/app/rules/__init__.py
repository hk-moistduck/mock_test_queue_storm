"""Rule data: keyword sets and compiled regex patterns.

Each case_type has:
- A frozenset of keywords (lower-signal)
- A list of compiled regex patterns (higher-signal, used first)

Adding a new rule is a data change, not a code change.
"""

from app.rules.keywords import (
    CRITICAL_KEYWORDS,
    ESCALATE_KEYWORDS,
    PAYMENT_FAILED_KEYWORDS,
    PHISHING_KEYWORDS,
    REFUND_REQUEST_KEYWORDS,
    WRONG_TRANSFER_KEYWORDS,
)
from app.rules.patterns import (
    PAYMENT_FAILED_PATTERNS,
    PHISHING_PATTERNS,
    REFUND_REQUEST_PATTERNS,
    SAFETY_DENY_PATTERNS,
    SAFETY_REPLACEMENTS,
    WRONG_TRANSFER_PATTERNS,
)

__all__ = [
    "CRITICAL_KEYWORDS",
    "ESCALATE_KEYWORDS",
    "PAYMENT_FAILED_KEYWORDS",
    "PAYMENT_FAILED_PATTERNS",
    "PHISHING_KEYWORDS",
    "PHISHING_PATTERNS",
    "REFUND_REQUEST_KEYWORDS",
    "REFUND_REQUEST_PATTERNS",
    "SAFETY_DENY_PATTERNS",
    "SAFETY_REPLACEMENTS",
    "WRONG_TRANSFER_KEYWORDS",
    "WRONG_TRANSFER_PATTERNS",
]