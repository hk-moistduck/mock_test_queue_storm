"""Compiled regex patterns.

All patterns are compiled once at import time with `re.IGNORECASE` so matching
is case-insensitive and fast.

Two pattern families:
- Classification patterns: high-signal patterns for case_type detection.
- Safety patterns: deny-list patterns used by the safety filter.
"""

from __future__ import annotations

import re

# ---------- Phishing patterns (checked first) ----------


PHISHING_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bhttps?://(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|is\.gd|ow\.ly|buff\.ly)/\S+", re.IGNORECASE),
    re.compile(r"\bhttps?://(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?(?:/\S*)?\b"),
    re.compile(r"\b[a-z0-9-]+\.(?:xyz|top|click|loan|work|country|kim|men|rest|zip|tk|ml|ga|cf)\b", re.IGNORECASE),
    re.compile(r"\b(?:urgent|immediate|action required)\b[^.\n]{0,80}\b(?:verify|click|login|confirm|update)\b", re.IGNORECASE),
    re.compile(r"\b(?:won|winner|prize|lottery|inheritance|million)\b[^.\n]{0,80}\b(?:claim|collect|transfer)\b", re.IGNORECASE),
    re.compile(r"\baccount\s+(?:has been\s+)?(?:locked|suspended|limited|restricted)\b", re.IGNORECASE),
    re.compile(r"\bverify\s+(?:your\s+)?(?:account|identity|login|email|password)\b", re.IGNORECASE),
)

# ---------- Wrong-transfer patterns ----------


WRONG_TRANSFER_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(?:wrong|mistaken|accidental|incorrect)\s+(?:transfer|transaction|payment)\b", re.IGNORECASE),
    re.compile(r"\b(?:transfer|transaction|payment|wire)\s+to\s+(?:the\s+)?(?:wrong|incorrect)\b", re.IGNORECASE),
    re.compile(r"\b(?:sent|transferred|paid|wired)\s+(?:it\s+|money\s+)?to\s+(?:the\s+)?(?:wrong|incorrect|unknown|stranger)\b", re.IGNORECASE),
    re.compile(r"\bintended\s+(?:recipient|account|person)\b", re.IGNORECASE),
    re.compile(r"\bunauthori[sz]ed\s+(?:transfer|transaction|payment)\b", re.IGNORECASE),
)

# ---------- Refund-request patterns ----------


REFUND_REQUEST_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\brefund\b", re.IGNORECASE),
    re.compile(r"\bmoney\s+back\b", re.IGNORECASE),
    re.compile(r"\bcharge\s*back\b", re.IGNORECASE),
    re.compile(r"\b(?:reverse|reversal\s+of)\s+(?:the\s+)?(?:charge|transaction|payment)\b", re.IGNORECASE),
    re.compile(r"\b(?:want|need|request(?:ing)?|asking\s+for)\s+(?:a\s+)?refund\b", re.IGNORECASE),
)

# ---------- Payment-failed patterns ----------


PAYMENT_FAILED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bpayment\s+(?:failed|declined|rejected|blocked|stuck|pending|error|not\s+\w+)\b", re.IGNORECASE),
    re.compile(r"\btransaction\s+(?:failed|declined|rejected|blocked|stuck|pending|error)\b", re.IGNORECASE),
    re.compile(r"\bcard\s+(?:declined|rejected|blocked|not\s+\w+)\b", re.IGNORECASE),
    re.compile(r"\b(?:charged|debited|deducted)\s+(?:twice|two\s+times|multiple\s+times|again)\b", re.IGNORECASE),
    re.compile(r"\b(?:double|duplicate)\s+(?:charge|charged|payment|payments)\b", re.IGNORECASE),
    re.compile(r"\b(?:insufficient|no|not\s+enough)\s+(?:funds|balance)\b", re.IGNORECASE),
)

# ---------- Safety deny-list (used by app.safety) ----------


#: Hard-deny patterns. If ANY of these still match after replacements, the
#: summary is replaced wholesale with a safe fallback.
SAFETY_DENY_PATTERNS: tuple[re.Pattern[str], ...] = (
    # "please share/provide/give/send/tell/enter/verify/confirm your/the PIN"
    re.compile(
        r"\b(?:please\s+|kindly\s+)?"
        r"(?:provide|share|give|send|tell|enter|type|input|verify|confirm|supply|disclose)\s+"
        r"(?:your|the|my)\s+"
        r"(?:pin|personal\s+identification\s+number)\b",
        re.IGNORECASE,
    ),
    # "please share/provide/give/send/tell/enter/verify/confirm your/the OTP"
    re.compile(
        r"\b(?:please\s+|kindly\s+)?"
        r"(?:provide|share|give|send|tell|enter|type|input|verify|confirm|supply|disclose)\s+"
        r"(?:your|the|my)\s+"
        r"(?:otp|one[\s-]?time\s+(?:password|code|pin)|verification\s+code|security\s+code|auth(?:entication)?\s+code)\b",
        re.IGNORECASE,
    ),
    # "please share/provide/give/send/tell/enter your/the password"
    re.compile(
        r"\b(?:please\s+|kindly\s+)?"
        r"(?:provide|share|give|send|tell|enter|type|input|supply|disclose)\s+"
        r"(?:your|the|my)\s+"
        r"(?:password|passcode|login\s+password|account\s+password)\b",
        re.IGNORECASE,
    ),
    # "please share/provide/give/send/tell us your/the card number"
    re.compile(
        r"\b(?:please\s+|kindly\s+)?"
        r"(?:provide|share|give|send|tell|enter|type|input|supply|disclose)\s+"
        r"(?:your|the|my)\s+"
        r"(?:card\s*number|credit\s+card|debit\s+card|full\s+card\s+number)\b",
        re.IGNORECASE,
    ),
    # PIN/OTP/Password followed by a digit run (i.e. an actual value)
    re.compile(r"\b(?:pin|otp|password|passcode)\s*[:\-]\s*\S+", re.IGNORECASE),
    # 13-19 digit card-number-like run
    re.compile(r"\b\d{13,19}\b"),
    # Grouped card-number-like run (4-4-4-... style with optional spaces or dashes)
    re.compile(r"\b(?:\d{4}[ -]?){3}\d{1,7}\b"),
)


#: Replacement rules applied first (from most specific to least specific).
#: Order matters — longer/more specific phrases are replaced before generic ones.
SAFETY_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Specific request phrases -> safe alternative
    (
        re.compile(
            r"\b(?:please\s+|kindly\s+)?"
            r"(?:share|provide|give|send|tell|enter|verify|confirm|supply|disclose)\s+"
            r"(?:your|the|my)\s+"
            r"(?:full\s+)?card\s+number\b",
            re.IGNORECASE,
        ),
        "do not share your card details",
    ),
    (
        re.compile(
            r"\b(?:please\s+|kindly\s+)?"
            r"(?:share|provide|give|send|tell|enter|verify|confirm|supply|disclose)\s+"
            r"(?:your|the|my)\s+"
            r"(?:pin|otp|one[\s-]?time\s+(?:password|code|pin)|verification\s+code|security\s+code|auth(?:entication)?\s+code)\b",
            re.IGNORECASE,
        ),
        "do not share your one-time credentials",
    ),
    (
        re.compile(
            r"\b(?:please\s+|kindly\s+)?"
            r"(?:share|provide|give|send|tell|enter|verify|confirm|supply|disclose)\s+"
            r"(?:your|the|my)\s+"
            r"(?:password|passcode|login\s+password|account\s+password)\b",
            re.IGNORECASE,
        ),
        "do not share your password",
    ),
    # Grouped card numbers -> [REDACTED-CARD]
    (re.compile(r"\b(?:\d{4}[ -]?){3}\d{1,7}\b"), "[REDACTED-CARD]"),
    # Bare 13-19 digit runs -> [REDACTED-CARD]
    (re.compile(r"\b\d{13,19}\b"), "[REDACTED-CARD]"),
    # Bare credential nouns -> credentials (lowest specificity, applied last)
    (
        re.compile(
            r"\b(?:otp|one[\s-]?time\s+(?:password|code|pin)|verification\s+code|security\s+code|auth(?:entication)?\s+code)\b",
            re.IGNORECASE,
        ),
        "credentials",
    ),
    (re.compile(r"\bpin\b", re.IGNORECASE), "credentials"),
    (re.compile(r"\b(?:password|passcode)\b", re.IGNORECASE), "credentials"),
)