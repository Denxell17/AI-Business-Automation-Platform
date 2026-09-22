"""Durable replay protection and metadata-only webhook delivery records."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TypedDict
from uuid import uuid4

from database import (
    DATABASE_FILE,
    insert_outbound_webhook_delivery,
    record_verified_inbound_webhook,
    record_verified_inbound_workflow_result,
)
from models import WebhookDelivery, WebhookReplayEvent
from webhook_contract import (
    WebhookEnvelope,
    validate_webhook_envelope,
    verify_inbound_webhook,
)


class InboundWebhookAcceptance(TypedDict):
    accepted: bool
    duplicate: bool
    envelope: WebhookEnvelope


class InboundWorkflowResult(TypedDict):
    applied: bool
    duplicate: bool
    not_applicable: bool


def _timestamp(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("Webhook time must include a time zone.")
    return value.astimezone(timezone.utc).isoformat()


def _inbound_records(
    envelope: WebhookEnvelope,
    current_time: datetime,
) -> tuple[WebhookReplayEvent, WebhookDelivery]:
    received_at = _timestamp(current_time)
    replay_event: WebhookReplayEvent = {
        "event_id": envelope["event_id"],
        "received_at": received_at,
        "expires_at": received_at,
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
    return replay_event, delivery


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
    replay_event, delivery = _inbound_records(envelope, current_time)
    replay_event["expires_at"] = _timestamp(
        current_time.astimezone(timezone.utc)
        + timedelta(seconds=signature_ttl_seconds),
    )
    accepted = record_verified_inbound_webhook(
        replay_event, delivery, database_file,
    )
    return {
        "accepted": accepted,
        "duplicate": not accepted,
        "envelope": envelope,
    }


def apply_verified_inbound_workflow_result(
    envelope: WebhookEnvelope,
    current_time: datetime,
    signature_ttl_seconds: int,
    database_file: Path = DATABASE_FILE,
) -> InboundWorkflowResult:
    """Apply one narrow, pre-verified integration outcome atomically."""
    validated = validate_webhook_envelope(envelope)
    data = validated["data"]
    if (
        validated["event_type"] != "workflow.execution.result"
        or set(data) != {"status"}
        or data["status"] not in {"completed", "failed"}
    ):
        raise ValueError("Webhook result callback is not supported.")
    if signature_ttl_seconds <= 0:
        raise ValueError("Webhook signature TTL must be positive.")
    replay_event, delivery = _inbound_records(validated, current_time)
    replay_event["expires_at"] = _timestamp(
        current_time.astimezone(timezone.utc)
        + timedelta(seconds=signature_ttl_seconds),
    )
    result_status = data["status"]
    outcome = record_verified_inbound_workflow_result(
        replay_event,
        delivery,
        validated["correlation_id"],
        result_status,
        _timestamp(current_time),
        f"{result_status.title()} by signed integration callback.",
        database_file,
    )
    return {
        "applied": outcome == "applied",
        "duplicate": outcome == "duplicate",
        "not_applicable": outcome == "not_applicable",
    }


def prepare_outbound_webhook_delivery(
    envelope: WebhookEnvelope,
    current_time: datetime,
    database_file: Path = DATABASE_FILE,
) -> str | None:
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
    if not insert_outbound_webhook_delivery(delivery, database_file):
        return None
    return delivery["delivery_id"]


def queue_outbound_webhook_delivery(
    envelope: WebhookEnvelope,
    current_time: datetime,
    database_file: Path = DATABASE_FILE,
) -> bool:
    """Compatibility wrapper for callers that only need queued/not queued."""
    return prepare_outbound_webhook_delivery(
        envelope, current_time, database_file,
    ) is not None
