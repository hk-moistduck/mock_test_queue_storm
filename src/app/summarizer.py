"""Rule-based agent_summary builder.

No LLM, no generation. Pure template strings chosen by case_type. The templates
are designed to NEVER contain request verbs adjacent to credential nouns — the
safety filter is the second line of defense.
"""

from __future__ import annotations

import re
from typing import Optional

from app.schemas import CaseType, Severity

#: Truncation length for agent_summary. Slightly under the 280-char ceiling.
MAX_SUMMARY_CHARS = 280

#: Extract a currency amount (optional) for the summary. Matches things like
#: "$49.99", "৳500", "€10", "49.99 usd", "1,200.50 taka", "500 bdt".
_AMOUNT_RE = re.compile(
    r"(?:[\$£€৳]\s?(\d[\d,]*(?:\.\d{1,2})?))|"
    r"\b(\d[\d,]*(?:\.\d{1,2})?)\s?(?:usd|eur|gbp|bdt|tk|inr|rs|dollar|euro|pound|taka|rupi|rupee)\b",
    re.IGNORECASE,
)


def _extract_amount(message: str) -> Optional[str]:
    """Return a human-friendly amount string if one is found, else None."""
    m = _AMOUNT_RE.search(message)
    if not m:
        return None
    raw = m.group(1) or m.group(2) or ""
    if not raw:
        return None
    return raw.replace(",", "")


def _truncate(text: str, max_chars: int = MAX_SUMMARY_CHARS) -> str:
    """Truncate at a word boundary, appending an ellipsis if cut."""
    if len(text) <= max_chars:
        return text
    truncated = text[: max_chars - 1].rsplit(" ", 1)[0]
    return (truncated or text[: max_chars - 1]) + "\u2026"


def _safe_context(message: str) -> str:
    """Return an optional context fragment based on amount present, e.g. ' of $49.99'."""
    amount = _extract_amount(message)
    return f" of {amount}" if amount else ""


def build_summary(
    message: str,
    case_type: CaseType,
    severity: Severity,
    channel: Optional[str] = None,
) -> str:
    """Build a short, safe agent_summary for a classified ticket.

    The output is template-driven and never contains request verbs. The safety
    filter is still applied as a final pass by the orchestrator.
    """
    ctx = _safe_context(message)
    channel_fragment = ""
    if channel:
        channel_fragment = f" via {channel}"

    if case_type == CaseType.PHISHING_OR_SOCIAL_ENGINEERING:
        text = (
            "Customer reports a potential phishing or social-engineering attempt"
            f"{channel_fragment}. "
            "Recommend escalating to fraud_risk and advising the customer not to click links, "
            "not to share codes, and to verify via official channels only."
        )
    elif case_type == CaseType.WRONG_TRANSFER:
        text = (
            "Customer reports a transfer sent to the wrong recipient or account"
            f"{channel_fragment}. "
            "Recommend initiating a bank recall or trace and collecting the intended recipient details."
        )
    elif case_type == CaseType.REFUND_REQUEST:
        text = (
            f"Customer is requesting a refund{ctx}{channel_fragment}. "
            "Recommend reviewing order history and processing the refund per policy."
        )
    elif case_type == CaseType.PAYMENT_FAILED:
        text = (
            f"Customer reports a payment failure{ctx}{channel_fragment}. "
            "Recommend verifying the transaction status with the payment provider "
            "and confirming the customer's account balance."
        )
    else:
        # CaseType.OTHER
        text = (
            "Customer reports an issue that does not match a known category"
            f"{channel_fragment}. "
            "Recommend gathering more details and routing to general customer support."
        )

    # Add a severity hint at the end so downstream agents see urgency in the summary.
    if severity == Severity.CRITICAL:
        text += " Severity: critical — prioritize immediately."
    elif severity == Severity.HIGH:
        text += " Severity: high — handle promptly."

    return _truncate(text, MAX_SUMMARY_CHARS)