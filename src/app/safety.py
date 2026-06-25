"""Safety filter — ensures the agent_summary never asks for sensitive credentials.

Two-layer defense (see README "Safety" section):

1. **Replacement pass.** Apply the ordered (specific → generic) replacement
   rules from SAFETY_REPLACEMENTS to the summary.
2. **Hard guard.** After replacements, if ANY SAFETY_DENY_PATTERNS still
   matches the text, replace the entire summary with a known-safe fallback.

The filter is deterministic, side-effect-free, and unit-testable.
"""

from __future__ import annotations

from app.rules import SAFETY_DENY_PATTERNS, SAFETY_REPLACEMENTS

#: The canonical safe fallback. Always safe; never contains request verbs.
SAFE_FALLBACK_SUMMARY: str = (
    "Issue acknowledged and queued for review. "
    "No sensitive credentials are required to proceed."
)


def sanitize_summary(text: str) -> str:
    """Sanitize an agent_summary so it never asks for sensitive credentials.

    Returns a safe string. If anything risky remains after the replacement
    pass, returns the canonical fallback.
    """
    if not text:
        return SAFE_FALLBACK_SUMMARY

    sanitized = text

    # Layer 1 — ordered replacements (specific -> generic)
    for pattern, replacement in SAFETY_REPLACEMENTS:
        sanitized = pattern.sub(replacement, sanitized)

    # Layer 2 — hard guard. If any deny pattern still matches, abort.
    for deny in SAFETY_DENY_PATTERNS:
        if deny.search(sanitized):
            return SAFE_FALLBACK_SUMMARY

    return sanitized