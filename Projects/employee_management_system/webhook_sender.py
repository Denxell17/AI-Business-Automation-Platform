"""Safe bounded outbound delivery for signed ABAP webhook messages."""

import http.client
import ipaddress
import socket
import ssl
import time
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Protocol, TypedDict
from urllib.parse import urlsplit

from database import DATABASE_FILE, record_outbound_webhook_attempt
from integration_config import IntegrationSettings
from webhook_contract import WebhookEnvelope, signed_webhook_headers
from webhook_delivery_service import prepare_outbound_webhook_delivery


class WebhookResponse(Protocol):
    status: int

    def read(self, amount: int = -1) -> bytes: ...


class WebhookConnection(Protocol):
    def request(
        self, method: str, url: str, body: bytes, headers: dict[str, str],
    ) -> None: ...

    def getresponse(self) -> WebhookResponse: ...

    def close(self) -> None: ...


class OutboundWebhookResult(TypedDict):
    sent: bool
    duplicate: bool
    delivery_id: str | None
    attempts: int


class _VerifiedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(
        self, hostname: str, port: int, address: str,
        connect_timeout_seconds: int, read_timeout_seconds: int,
    ) -> None:
        super().__init__(hostname, port=port, timeout=connect_timeout_seconds)
        self._verified_address = address
        self._read_timeout_seconds = read_timeout_seconds

    def connect(self) -> None:
        raw_socket = socket.create_connection(
            (self._verified_address, self.port), self.timeout,
        )
        context = ssl.create_default_context()
        self.sock = context.wrap_socket(raw_socket, server_hostname=self.host)
        self.sock.settimeout(self._read_timeout_seconds)


def resolve_public_addresses(
    hostname: str,
    port: int,
    resolver: Callable[..., list[tuple]] = socket.getaddrinfo,
) -> tuple[str, ...]:
    """Resolve a host immediately before connection and reject every unsafe IP."""
    try:
        records = resolver(hostname, port, type=socket.SOCK_STREAM)
    except OSError as error:
        raise ValueError("Webhook destination could not be resolved.") from error
    addresses = tuple(dict.fromkeys(record[4][0] for record in records))
    if not addresses:
        raise ValueError("Webhook destination could not be resolved.")
    try:
        if any(not ipaddress.ip_address(address).is_global for address in addresses):
            raise ValueError("Webhook destination resolved to a blocked address.")
    except ValueError as error:
        if str(error).startswith("Webhook destination"):
            raise
        raise ValueError("Webhook destination resolved to an invalid address.") from error
    return addresses


def _connection(
    hostname: str, port: int, address: str, connect_timeout_seconds: int,
    read_timeout_seconds: int,
) -> WebhookConnection:
    return _VerifiedHTTPSConnection(
        hostname, port, address, connect_timeout_seconds, read_timeout_seconds,
    )


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _next_attempt(current_time: datetime, attempt: int) -> str:
    return _timestamp(
        current_time.astimezone(timezone.utc)
        + timedelta(seconds=min(2 ** (attempt - 1), 8)),
    )


def _post_once(
    settings: IntegrationSettings,
    envelope: WebhookEnvelope,
    current_time: datetime,
    resolver: Callable[..., list[tuple]],
    connection_factory: Callable[..., WebhookConnection],
) -> tuple[bool, bool, int | None, str]:
    """Return succeeded, retryable, response status, and a safe failure code."""
    base_url = settings["base_url"]
    workflow_path = settings["workflow_path"]
    secret = settings["outbound_secret"]
    if not settings["enabled"] or not base_url or not workflow_path or not secret:
        raise ValueError("Outbound webhook integration is not enabled.")
    parsed = urlsplit(base_url)
    hostname = parsed.hostname
    if not hostname or hostname not in settings["allowed_hosts"]:
        raise ValueError("Outbound webhook destination is not allowlisted.")
    port = parsed.port or 443
    addresses = resolve_public_addresses(hostname, port, resolver)
    headers, body = signed_webhook_headers(
        secret, envelope, int(current_time.astimezone(timezone.utc).timestamp()),
    )
    if len(body) > settings["max_request_bytes"]:
        return False, False, None, "request_too_large"
    connection = connection_factory(
        hostname, port, addresses[0], settings["connect_timeout_seconds"],
        settings["read_timeout_seconds"],
    )
    try:
        connection.request(
            "POST", workflow_path, body,
            {
                "Content-Type": headers["content_type"],
                "X-ABAP-Timestamp": headers["timestamp"],
                "X-ABAP-Event-Id": headers["event_id"],
                "X-ABAP-Signature": headers["signature"],
            },
        )
        response = connection.getresponse()
        if len(response.read(settings["max_response_bytes"] + 1)) > settings["max_response_bytes"]:
            return False, False, response.status, "response_too_large"
        if 200 <= response.status < 300:
            return True, False, response.status, ""
        if 300 <= response.status < 400:
            return False, False, response.status, "redirect_blocked"
        if 400 <= response.status < 500:
            return False, False, response.status, "http_4xx"
        return False, True, response.status, "http_5xx"
    except (OSError, TimeoutError, ssl.SSLError, http.client.HTTPException) as error:
        if isinstance(error, (socket.timeout, TimeoutError)):
            return False, True, None, "timeout"
        return False, True, None, "network_error"
    finally:
        connection.close()


def deliver_outbound_webhook(
    settings: IntegrationSettings,
    envelope: WebhookEnvelope,
    current_time: datetime,
    database_file: Path = DATABASE_FILE,
    resolver: Callable[..., list[tuple]] = socket.getaddrinfo,
    connection_factory: Callable[..., WebhookConnection] = _connection,
    sleep: Callable[[float], None] = time.sleep,
) -> OutboundWebhookResult:
    """Send one event with bounded in-memory retries and durable status updates."""
    if not isinstance(current_time, datetime) or current_time.tzinfo is None:
        raise ValueError("Webhook time must include a time zone.")
    if (
        not settings["enabled"] or not settings["base_url"]
        or not settings["workflow_path"] or not settings["outbound_secret"]
    ):
        raise ValueError("Outbound webhook integration is not enabled.")
    delivery_id = prepare_outbound_webhook_delivery(
        envelope, current_time, database_file,
    )
    if delivery_id is None:
        return {"sent": False, "duplicate": True, "delivery_id": None, "attempts": 0}
    for attempt in range(1, settings["max_attempts"] + 1):
        try:
            succeeded, retryable, response_status, failure_code = _post_once(
                settings, envelope, current_time, resolver, connection_factory,
            )
        except ValueError:
            succeeded, retryable, response_status, failure_code = (
                False, False, None, "destination_blocked",
            )
        if succeeded:
            record_outbound_webhook_attempt(
                delivery_id, "succeeded", _timestamp(current_time), response_status,
                "", None, database_file,
            )
            return {"sent": True, "duplicate": False, "delivery_id": delivery_id, "attempts": attempt}
        if retryable and attempt < settings["max_attempts"]:
            record_outbound_webhook_attempt(
                delivery_id, "retrying", _timestamp(current_time), response_status,
                failure_code, _next_attempt(current_time, attempt), database_file,
            )
            sleep(min(2 ** (attempt - 1), 8))
            continue
        record_outbound_webhook_attempt(
            delivery_id, "failed", _timestamp(current_time), response_status,
            failure_code, None, database_file,
        )
        return {"sent": False, "duplicate": False, "delivery_id": delivery_id, "attempts": attempt}
    raise RuntimeError("Outbound webhook attempts did not reach a terminal state.")
