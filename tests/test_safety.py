"""Safety filter tests — the most important invariants in the system.

The safety filter MUST ensure that agent_summary never asks for:
  - PIN
  - OTP / one-time password / verification code
  - Password / passcode
  - Full card number

And MUST redact card-number-like digit runs.
"""

from __future__ import annotations

import pytest

from app.safety import SAFE_FALLBACK_SUMMARY, sanitize_summary
from app.rules import SAFETY_DENY_PATTERNS


# ---------- Unit tests on sanitize_summary directly ----------


def test_sanitize_replaces_share_your_pin():
    out = sanitize_summary("Please share your PIN to verify.")
    assert "pin" not in out.lower()
    assert "credentials" in out.lower() or "do not share" in out.lower()


def test_sanitize_replaces_provide_your_otp():
    out = sanitize_summary("You must provide your OTP now.")
    # After replacement, "OTP" should be replaced with "credentials" or the
    # request verb phrase should be neutralized.
    assert "provide your otp" not in out.lower()
    assert "otp" not in out.lower() or "credentials" in out.lower()


def test_sanitize_replaces_enter_your_password():
    out = sanitize_summary("Please enter your password to continue.")
    assert "enter your password" not in out.lower()


def test_sanitize_redacts_card_number_grouped():
    out = sanitize_summary("Send your card number 4111 1111 1111 1111 to support.")
    assert "4111 1111 1111 1111" not in out
    assert "[REDACTED-CARD]" in out


def test_sanitize_redacts_card_number_dashed():
    out = sanitize_summary("Card 4111-1111-1111-1111 was charged.")
    assert "4111-1111-1111-1111" not in out
    assert "[REDACTED-CARD]" in out


def test_sanitize_redacts_bare_digit_run():
    out = sanitize_summary("My number is 4111111111111111 please.")
    assert "4111111111111111" not in out
    assert "[REDACTED-CARD]" in out


def test_sanitize_returns_safe_fallback_on_unrecoverable():
    """If something still matches a deny pattern, the whole summary is replaced."""
    # Construct something that the replacement can't fully neutralize.
    tricky = "Provide your pin: 1234 now please."
    out = sanitize_summary(tricky)
    # Either the replacement caught it or the fallback fired.
    assert not any(p.search(out) for p in SAFETY_DENY_PATTERNS)


def test_sanitize_passes_clean_text_through():
    clean = "Customer reports a payment failure of $49.99."
    out = sanitize_summary(clean)
    assert out == clean


def test_safe_fallback_is_actually_safe():
    """The fallback summary itself never matches a deny pattern."""
    for p in SAFETY_DENY_PATTERNS:
        assert not p.search(SAFE_FALLBACK_SUMMARY)


# ---------- End-to-end safety over the API ----------


@pytest.mark.asyncio
async def test_e2e_summary_never_asks_for_pin(client):
    """Even when the customer message mentions a PIN, the summary stays safe."""
    response = await client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-SAFE-1",
            "message": "Phishing email asked for my PIN to verify my account.",
        },
    )
    body = response.json()
    summary = body["agent_summary"].lower()
    # No "share/provide/give/... your/the pin" construction
    for verb in ("share", "provide", "give", "send", "tell", "enter", "verify", "confirm"):
        assert f"{verb} your pin" not in summary
        assert f"{verb} the pin" not in summary


@pytest.mark.asyncio
async def test_e2e_summary_redacts_card_numbers(client):
    """Card numbers in the message are never echoed into the summary.

    Safety guarantee: no card-number-like digit runs appear in the summary,
    in any form (raw, grouped with spaces, grouped with dashes). The summary
    templates don't echo message content, so the digits never reach the
    output. We assert the actual invariant — no digits — rather than
    expecting a redaction marker (which is an implementation detail).
    """
    response = await client.post(
        "/sort-ticket",
        json={
            "ticket_id": "T-SAFE-2",
            "message": "My card 4111 1111 1111 1111 was charged twice, payment failed.",
        },
    )
    summary = response.json()["agent_summary"]

    # The digits must not appear in any common card-number form.
    assert "4111" not in summary
    assert "4111-1111-1111-1111" not in summary
    # No 13-19 digit runs at all (catches any other card-like number).
    assert not any(
        len(token) >= 13 and token.isdigit()
        for token in summary.split()
    ), f"Summary contains an unexpected digit run: {summary!r}"
