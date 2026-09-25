"""Versioned, signed webhook messages with strict parsing boundaries."""

import hashlib
import hmac
import json
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any, TypedDict
from uuid import UUID


WEBHOOK_SCHEMA_VERSION = "abap.webhook.v1"
WEBHOOK_CONTENT_TYPE = "application/json"
SIGNATURE_PREFIX = "v1="
MAX_EVENT_TYPE_LENGTH = 80
MAX_CORRELATION_ID_LENGTH = 128
_EVENT_TYPE = re.compile(r"^[a-z][a-z0-9]*(?:\.[a-z][a-z0-9]*){1,5}$")
_CORRELATION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")


class WebhookEnvelope(TypedDict):
    schema_version: str
    event_id: str
    correlation_id: str
    event_type: str
    occurred_at: str
    data: dict[str, Any]


class WebhookHeaders(TypedDict):
    content_type: str
    timestamp: str
    event_id: str
    signature: str


def _require_secret(secret: str) -> bytes:
    if not isinstance(secret, str) or not secret:
        raise ValueError("Webhook signing secret is required.")
    return secret.encode("utf-8")


def _canonical_event_id(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Webhook event ID must be a UUID.")
    try:
        identifier = UUID(value)
    except ValueError as error:
        raise ValueError("Webhook event ID must be a UUID.") from error
    if str(identifier) != value:
        raise ValueError("Webhook event ID must use canonical UUID form.")
    return str(identifier)


def _validate_event_type(value: object) -> str:
    if (
        not isinstance(value, str)
        or len(value) > MAX_EVENT_TYPE_LENGTH
        or not _EVENT_TYPE.fullmatch(value)
    ):
        raise ValueError("Webhook event type is invalid.")
    return value


def _validate_correlation_id(value: object) -> str:
    if (
        not isinstance(value, str)
        or len(value) > MAX_CORRELATION_ID_LENGTH
        or not _CORRELATION_ID.fullmatch(value)
    ):
        raise ValueError("Webhook correlation ID is invalid.")
    return value


def _canonical_occurred_at(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Webhook occurred_at must be an ISO-8601 timestamp.")
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Webhook occurred_at must be an ISO-8601 timestamp.") from error
    if timestamp.tzinfo is None:
        raise ValueError("Webhook occurred_at must include a time zone.")
    return timestamp.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def validate_webhook_envelope(value: object) -> WebhookEnvelope:
    """Validate the complete public message shape before it reaches services."""
    if not isinstance(value, dict) or set(value) != {
        "schema_version", "event_id", "correlation_id", "event_type",
        "occurred_at", "data",
    }:
        raise ValueError("Webhook envelope has an invalid shape.")
    if value["schema_version"] != WEBHOOK_SCHEMA_VERSION:
        raise ValueError("Webhook schema version is unsupported.")
    if not isinstance(value["data"], dict):
        raise ValueError("Webhook data must be a JSON object.")
    envelope: WebhookEnvelope = {
        "schema_version": WEBHOOK_SCHEMA_VERSION,
        "event_id": _canonical_event_id(value["event_id"]),
        "correlation_id": _validate_correlation_id(value["correlation_id"]),
        "event_type": _validate_event_type(value["event_type"]),
        "occurred_at": _canonical_occurred_at(value["occurred_at"]),
        "data": value["data"],
    }
    try:
        canonical_json_bytes(envelope)
    except (TypeError, ValueError) as error:
        raise ValueError("Webhook data must contain JSON values only.") from error
    return envelope


def canonical_json_bytes(value: object) -> bytes:
    """Return the one JSON representation used for signatures and size checks."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def build_webhook_envelope(
    event_id: str,
    correlation_id: str,
    event_type: str,
    occurred_at: datetime,
    data: Mapping[str, Any],
) -> WebhookEnvelope:
    """Build a validated envelope from trusted application data."""
    if not isinstance(occurred_at, datetime) or occurred_at.tzinfo is None:
        raise ValueError("Webhook occurred_at must include a time zone.")
    envelope = {
        "schema_version": WEBHOOK_SCHEMA_VERSION,
        "event_id": event_id,
        "correlation_id": correlation_id,
        "event_type": event_type,
        "occurred_at": occurred_at.astimezone(timezone.utc).isoformat().replace(
            "+00:00", "Z",
        ),
        "data": dict(data),
    }
    return validate_webhook_envelope(envelope)


def sign_webhook_body(
    secret: str, timestamp: int, event_id: str, body: bytes,
) -> str:
    """Sign an exact body with headers that prevent cross-event substitution."""
    if not isinstance(timestamp, int) or timestamp < 0:
        raise ValueError("Webhook timestamp must be a non-negative integer.")
    if not isinstance(body, bytes):
        raise ValueError("Webhook body must be bytes.")
    event = _canonical_event_id(event_id)
    signed = b"\n".join((
        WEBHOOK_SCHEMA_VERSION.encode("ascii"), str(timestamp).encode("ascii"),
        event.encode("ascii"), body,
    ))
    digest = hmac.new(_require_secret(secret), signed, hashlib.sha256).hexdigest()
    return f"{SIGNATURE_PREFIX}{digest}"


def signed_webhook_headers(
    secret: str, envelope: WebhookEnvelope, timestamp: int,
) -> tuple[WebhookHeaders, bytes]:
    """Build the exact headers and bytes an outbound HTTP client will send."""
    validated = validate_webhook_envelope(envelope)
    body = canonical_json_bytes(validated)
    return {
        "content_type": WEBHOOK_CONTENT_TYPE,
        "timestamp": str(timestamp),
        "event_id": validated["event_id"],
        "signature": sign_webhook_body(secret, timestamp, validated["event_id"], body),
    }, body


def verify_inbound_webhook(
    headers: Mapping[str, object], body: bytes, secret: str,
    current_time: datetime, signature_ttl_seconds: int, max_request_bytes: int,
) -> WebhookEnvelope:
    """Verify a request completely before returning its parsed envelope."""
    if not isinstance(body, bytes) or len(body) > max_request_bytes:
        raise ValueError("Webhook request body exceeds the allowed size.")
    if not isinstance(current_time, datetime) or current_time.tzinfo is None:
        raise ValueError("Current time must include a time zone.")
    if signature_ttl_seconds <= 0:
        raise ValueError("Webhook signature TTL must be positive.")
    content_type = headers.get("content_type")
    timestamp_text = headers.get("timestamp")
    event_id = headers.get("event_id")
    signature = headers.get("signature")
    if content_type != WEBHOOK_CONTENT_TYPE:
        raise ValueError("Webhook content type is unsupported.")
    if not isinstance(timestamp_text, str) or not timestamp_text.isdecimal():
        raise ValueError("Webhook timestamp is invalid.")
    timestamp = int(timestamp_text)
    now = int(current_time.astimezone(timezone.utc).timestamp())
    if timestamp < now - signature_ttl_seconds or timestamp > now + 60:
        raise ValueError("Webhook timestamp is outside the allowed window.")
    canonical_event = _canonical_event_id(event_id)
    if not isinstance(signature, str) or not signature.startswith(SIGNATURE_PREFIX):
        raise ValueError("Webhook signature is invalid.")
    expected = sign_webhook_body(secret, timestamp, canonical_event, body)
    if not hmac.compare_digest(expected, signature):
        raise ValueError("Webhook signature is invalid.")
    try:
        decoded = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Webhook body must be valid JSON.") from error
    envelope = validate_webhook_envelope(decoded)
    if envelope["event_id"] != canonical_event:
        raise ValueError("Webhook event ID does not match its header.")
    return envelope
