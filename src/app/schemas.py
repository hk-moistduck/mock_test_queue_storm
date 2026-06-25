"""Pydantic v2 schemas and enums for the API.

These models are the *contract* between the service and the outside world.
`extra="forbid"` rejects unknown fields so client mistakes fail loudly.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------- Enums (serialized as plain strings) ----------


class CaseType(str, Enum):
    """The 5 case categories per task spec."""

    WRONG_TRANSFER = "wrong_transfer"
    PAYMENT_FAILED = "payment_failed"
    REFUND_REQUEST = "refund_request"
    PHISHING_OR_SOCIAL_ENGINEERING = "phishing_or_social_engineering"
    OTHER = "other"


class Severity(str, Enum):
    """Ordered: low < medium < high < critical."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Department(str, Enum):
    """Routing targets per task spec."""

    CUSTOMER_SUPPORT = "customer_support"
    DISPUTE_RESOLUTION = "dispute_resolution"
    PAYMENTS_OPS = "payments_ops"
    FRAUD_RISK = "fraud_risk"


# ---------- Request ----------


class SortTicketRequest(BaseModel):
    """Inbound CRM ticket payload.

    `ticket_id` and `message` are required; `channel` and `locale` are optional
    metadata that may help downstream routing but are not used for classification.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        str_max_length=5000,
    )

    ticket_id: str = Field(..., min_length=1, max_length=128, description="Unique ticket identifier.")
    channel: Optional[str] = Field(default=None, max_length=64, description="Originating channel (email, chat, phone, etc.).")
    locale: Optional[str] = Field(default=None, max_length=16, description="BCP-47 locale tag, e.g. en-US, bn-BD.")
    message: str = Field(..., min_length=1, max_length=5000, description="Free-text ticket body.")

    @field_validator("message", mode="before")
    @classmethod
    def _normalize_message(cls, v: object) -> object:
        """Collapse runs of whitespace (including newlines) into single spaces."""
        if isinstance(v, str):
            return " ".join(v.split())
        return v


# ---------- Response ----------


class SortTicketResponse(BaseModel):
    """Outbound classification result.

    Field order is the documented API order. The model is frozen via
    `extra="forbid"` to catch accidental additions.
    """

    model_config = ConfigDict(extra="forbid")

    ticket_id: str
    case_type: CaseType
    severity: Severity
    department: Department
    agent_summary: str
    human_review_required: bool
    confidence: float = Field(..., ge=0.0, le=1.0)


# ---------- Health ----------


class HealthResponse(BaseModel):
    """Health check response."""

    model_config = ConfigDict(extra="forbid")

    status: str
    service: str
    version: str
    uptime_seconds: float
    timestamp: str