"""Keyword sets for classification and severity.

All keywords are stored lowercased; matching is case-insensitive at the call site.
frozenset for O(1) membership tests and immutability.
"""

from __future__ import annotations

# ---------- Classification keywords ----------


#: Phishing / social-engineering indicators. Highest priority.
PHISHING_KEYWORDS: frozenset[str] = frozenset(
    {
        "phishing", "phish", "phished",
        "scam", "scammer", "scammed",
        "fraud", "fraudulent",
        "impersonat", "impersonation", "impersonator",
        "fake email", "fake sms", "fake message", "fake call",
        "suspicious link", "suspicious email", "suspicious message", "suspicious text",
        "social engineering",
        "pretend to be", "pretending to be", "posed as", "posing as",
        "asked for otp", "asked for pin", "asked for password",
        "asked me to verify", "verify your account", "verify your identity",
        "click here to verify",
        "unauthorized access", "unauthorized transaction", "unauthorised access", "unauthorised transaction",
        "account compromised", "compromised account",
        "hacked", "got hacked", "account hacked",
        "stolen card", "card stolen",
        "identity theft", "identity stolen",
        "wire transfer scam", "gift card scam", "romance scam",
        "tech support scam",
        "irs scam", "tax scam",
        "lottery scam", "inheritance scam", "prize scam",
    }
)

#: Wrong-transfer indicators.
WRONG_TRANSFER_KEYWORDS: frozenset[str] = frozenset(
    {
        "wrong transfer", "wrong transaction", "wrong payment",
        "mistaken transfer", "mistakenly transferred", "mistaken transaction",
        "accidental transfer", "accidentally transferred", "accidental transaction",
        "sent to wrong person", "sent money to wrong", "paid wrong person",
        "wrong account", "wrong recipient", "wrong beneficiary",
        "transferred to wrong", "wired to wrong",
        "money sent to wrong", "funds sent to wrong",
        "transfer to wrong", "transferred by mistake", "sent by mistake",
        "i sent it to the wrong", "i paid the wrong",
        "sent to a stranger", "sent to unknown person",
        "stranger received", "not the intended",
        "intended recipient", "intended account", "intended person",
        "recall the transfer", "recall transfer", "cancel transfer", "cancel the transfer",
        "bank recall", "recall request",
        "unauthorized transfer", "unauthorised transfer",
    }
)

#: Refund-request indicators.
REFUND_REQUEST_KEYWORDS: frozenset[str] = frozenset(
    {
        "refund", "refunds", "refunded",
        "reimburse", "reimbursement", "reimbursed",
        "money back", "want my money back", "want my money",
        "chargeback", "charge back",
        "return my money", "give my money back",
        "refund my order", "refund the order", "refund please", "please refund",
        "i want a refund", "i want my refund", "request a refund", "refund request",
        "reversal", "reverse the charge", "reverse transaction", "reverse the payment",
        "cancel and refund", "refund processed", "refund pending",
        "still waiting for refund", "haven't received my refund", "have not received my refund",
    }
)

#: Payment-failed indicators.
PAYMENT_FAILED_KEYWORDS: frozenset[str] = frozenset(
    {
        "payment failed", "payment not going through", "payment not working",
        "payment declined", "payment was declined", "payment rejected",
        "transaction failed", "transaction declined", "transaction rejected",
        "transaction not going through", "transaction not working",
        "card declined", "card was declined", "card not working", "card rejected",
        "declined card", "declined transaction",
        "insufficient funds", "insufficient balance", "no balance", "not enough funds",
        "could not complete payment", "unable to complete payment",
        "unable to process payment", "payment processing error",
        "double charge", "double charged", "charged twice", "charged two times",
        "duplicate charge", "duplicate payment", "charged multiple times",
        "payment pending", "payment stuck", "stuck on payment", "payment on hold",
        "blocked payment", "payment blocked", "blocked transaction",
        "payment not received", "merchant not received", "did not receive payment",
        "money deducted", "amount deducted", "deducted but not received",
        "but not credited", "but i paid", "but i have paid",
        "upi failed", "upi not working", "bkash failed", "nagad failed",
        "rocket failed", "stripe failed", "razorpay failed", "paypal failed",
        "error code", "payment error", "checkout error",
        "3ds", "3-d secure", "3d secure",
        "authentication failed", "bank authentication",
    }
)

# ---------- Severity keywords ----------


#: If any of these appear, force severity to CRITICAL.
CRITICAL_KEYWORDS: frozenset[str] = frozenset(
    {
        "account hacked", "account compromised", "compromised",
        "all my money lost", "lost all my money", "drained my account",
        "identity theft", "identity stolen",
        "police report", "filed a report", "law enforcement",
        "lawsuit", "legal action", "court",
        "stolen", "card stolen", "card was stolen",
        "phishing", "phish", "scam", "scammer", "fraud", "fraudulent",
        "social engineering",
        "unauthorized transaction", "unauthorised transaction",
        "unauthorized access", "unauthorised access",
        "got hacked", "hacked",
    }
)

#: If any of these appear and CRITICAL didn't fire, bump severity one tier.
ESCALATE_KEYWORDS: frozenset[str] = frozenset(
    {
        "urgent", "urgently", "immediately", "asap", "right now",
        "emergency", "critical",
        "blocked", "stuck",
        "lost access", "locked out", "cannot login", "can't log in", "cant login",
        "account closed", "account suspended",
        "police", "lawsuit", "legal action",
        "double charged", "charged twice", "multiple times",
        "large amount", "big amount", "huge", "thousands",
        "no response", "no reply", "days now", "weeks now", "weeks already",
        "all my money", "lost money", "money lost",
    }
)