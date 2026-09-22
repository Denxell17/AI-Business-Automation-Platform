"""Durable replay protection and metadata-only webhook delivery records."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from database import (
    DATABASE_FILE,
    insert_outbound_webhook_delivery,
    record_verified_inbound_webhook,
)
from models import WebhookDelivery, WebhookReplayEvent
from webhook_contract import WebhookEnvelope, verify_inbound_webhook


class InboundWebhookAcceptance(TypedDict):
    accepted: bool
    duplicate: bool
    envelope: WebhookEnvelope


def _timestamp(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("Webhook time must include a time zone.")
    return value.astimezone(timezone.utc).isoformat()


def accept_inbound_webhook(
    headers: dict[str, object],
    body: bytes,
    inbound_secret: str,
    current_time: datetime,
    signature_ttl_seconds: int,
    max_request_bytes: int,
    database_file: Path = DATABASE_FILE,
) -> InboundWebhookAcceptance:
    """Verify then atomically claim an event before a future handler uses it."""
    envelope = verify_inbound_webhook(
        headers, body, inbound_secret, current_time, signature_ttl_seconds,
        max_request_bytes,
    )
    received_at = _timestamp(current_time)
    expires_at = _timestamp(
        current_time.astimezone(timezone.utc)
        + timedelta(seconds=signature_ttl_seconds),
    )
    replay_event: WebhookReplayEvent = {
        "event_id": envelope["event_id"],
        "received_at": received_at,
        "expires_at": expires_at,
    }
    delivery: WebhookDelivery = {
        "delivery_id": f"WHD-{uuid4().hex.upper()}",
        "direction": "inbound",
        "event_id": envelope["event_id"],
        "correlation_id": envelope["correlation_id"],
        "event_type": envelope["event_type"],
        "status": "accepted",
        "attempt_count": 1,
        "next_attempt_at": None,
        "response_status": None,
        "failure_code": "",
        "created_at": received_at,
        "updated_at": received_at,
        "completed_at": received_at,
    }
    accepted = record_verified_inbound_webhook(
        replay_event, delivery, database_file,
    )
    return {
        "accepted": accepted,
        "duplicate": not accepted,
        "envelope": envelope,
    }


def queue_outbound_webhook_delivery(
    envelope: WebhookEnvelope,
    current_time: datetime,
    database_file: Path = DATABASE_FILE,
) -> bool:
    """Persist a send-ready record without payload, secret, or destination data."""
    created_at = _timestamp(current_time)
    delivery: WebhookDelivery = {
        "delivery_id": f"WHD-{uuid4().hex.upper()}",
        "direction": "outbound",
        "event_id": envelope["event_id"],
        "correlation_id": envelope["correlation_id"],
        "event_type": envelope["event_type"],
        "status": "pending",
        "attempt_count": 0,
        "next_attempt_at": created_at,
        "response_status": None,
        "failure_code": "",
        "created_at": created_at,
        "updated_at": created_at,
        "completed_at": None,
    }
    return insert_outbound_webhook_delivery(delivery, database_file)
