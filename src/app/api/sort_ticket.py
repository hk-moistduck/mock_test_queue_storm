"""POST /sort-ticket — classify a single CRM support ticket.

Contract:
  - Request:  SortTicketRequest (ticket_id, channel?, locale?, message)
  - Response: SortTicketResponse with classification, routing, summary, etc.
  - Latency:  target <30 seconds.
  - Errors:   422 for schema validation failures; 500 for unexpected.

Logging: one structured log line per request with the classification result
and latency. The raw message body is never logged — only its length and a
SHA-256 prefix for traceability.
"""

from __future__ import annotations

import hashlib
import time

from fastapi import APIRouter, Request

from app.classifier import process_ticket
from app.logging_config import get_logger
from app.schemas import SortTicketRequest, SortTicketResponse

router = APIRouter(tags=["tickets"])
log = get_logger()


@router.post(
    "/sort-ticket",
    response_model=SortTicketResponse,
    summary="Classify a single CRM support ticket",
)
async def sort_ticket(payload: SortTicketRequest, request: Request) -> SortTicketResponse:
    """Classify a CRM support ticket.

    The handler is intentionally thin — all logic lives in
    `app.classifier.process_ticket`. Latency is measured and logged.
    """
    started = time.perf_counter()

    response = process_ticket(payload)

    latency_ms = round((time.perf_counter() - started) * 1000, 2)
    msg_hash_prefix = hashlib.sha256(payload.message.encode("utf-8")).hexdigest()[:16]

    log.info(
        "sort_ticket_processed",
        ticket_id=payload.ticket_id,
        case_type=response.case_type.value,
        severity=response.severity.value,
        department=response.department.value,
        confidence=response.confidence,
        human_review_required=response.human_review_required,
        latency_ms=latency_ms,
        message_length=len(payload.message),
        message_sha256_prefix=msg_hash_prefix,
        channel=payload.channel,
        locale=payload.locale,
    )

    return response