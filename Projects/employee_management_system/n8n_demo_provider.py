"""Private durable trust boundary for the isolated n8n demonstration."""

import base64
import binascii
import hashlib
import hmac
import json
import os
import stat
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import urlsplit
from uuid import UUID, uuid5

import psycopg
from psycopg.rows import dict_row

from webhook_contract import (
    build_webhook_envelope,
    signed_webhook_headers,
    verify_inbound_webhook,
)


MAX_REQUEST_BYTES = 262_144
MAX_CALLBACK_RESPONSE_BYTES = 65_536
CALLBACK_NAMESPACE = UUID("d4515974-27cc-4f42-a4ed-873c4d9bd672")
EXPECTED_EVENT_TYPE = "workflow.execution.started"
ALLOWED_RESULTS = {"completed", "failed"}
PROVIDER_TOKEN_FILE = "/run/secrets/abap_n8n_provider_token"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _require_environment(name: str, minimum_length: int = 1) -> str:
    value = os.environ.get(name, "")
    if len(value) < minimum_length:
        raise RuntimeError(f"{name} is required for the isolated n8n demo.")
    return value


def _read_secret_file(path: str, minimum_length: int = 1) -> str:
    """Read a small, non-symlink secret without placing its value in the environment."""
    if not os.path.isabs(path):
        raise RuntimeError("Secret file path must be absolute.")
    try:
        metadata = os.lstat(path)
    except OSError as error:
        raise RuntimeError("Required provider-token secret file is unavailable.") from error
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError("Provider-token secret must be a regular file.")
    if metadata.st_size > 4096:
        raise RuntimeError("Provider-token secret file is too large.")
    try:
        with open(path, "rb") as secret_file:
            raw_value = secret_file.read(4097)
        value = raw_value.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise RuntimeError("Provider-token secret file could not be read safely.") from error
    value = value.removesuffix("\n").removesuffix("\r")
    if len(value) < minimum_length or any(character.isspace() for character in value):
        raise RuntimeError("Provider-token secret file contains an invalid token.")
    return value


def _canonical_uuid(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Event ID must be a canonical UUID.")
    try:
        identifier = UUID(value)
    except ValueError as error:
        raise ValueError("Event ID must be a canonical UUID.") from error
    if str(identifier) != value:
        raise ValueError("Event ID must be a canonical UUID.")
    return value


def _validate_started_event(envelope: dict[str, Any]) -> tuple[str, str]:
    data = envelope["data"]
    if (
        envelope["event_type"] != EXPECTED_EVENT_TYPE
        or set(data) != {"execution_id", "workflow_id", "trigger_type"}
        or not isinstance(data["execution_id"], str)
        or not isinstance(data["workflow_id"], str)
        or data["trigger_type"] not in {"schedule", "manual"}
        or envelope["correlation_id"] != data["execution_id"]
    ):
        raise ValueError("Webhook event is not a supported scheduled execution.")
    return data["execution_id"], data["workflow_id"]


def _validate_callback_url(value: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "http"
        or parsed.hostname != "web"
        or parsed.port != 8000
        or parsed.path != "/integrations/webhooks/callback"
        or parsed.query
        or parsed.fragment
        or parsed.username
        or parsed.password
    ):
        raise RuntimeError("ABAP_CALLBACK_URL must be the private ABAP callback endpoint.")
    return value


def _send_callback_once(
    url: str, headers: dict[str, str], body: bytes, timeout_seconds: float,
) -> int:
    request = urllib.request.Request(
        url, data=body, method="POST", headers={
            "Content-Type": headers["content_type"],
            "X-ABAP-Timestamp": headers["timestamp"],
            "X-ABAP-Event-Id": headers["event_id"],
            "X-ABAP-Signature": headers["signature"],
        },
    )
    try:
        opener = urllib.request.build_opener(_NoRedirect)
        with opener.open(request, timeout=timeout_seconds) as response:
            response.read(MAX_CALLBACK_RESPONSE_BYTES + 1)
            return response.status
    except urllib.error.HTTPError as error:
        error.read(MAX_CALLBACK_RESPONSE_BYTES + 1)
        return error.code


class N8nDemoEventStore:
    """PostgreSQL-backed idempotency, leases, and private callback state."""

    def __init__(self, database_url: str, connect_timeout_seconds: int = 2):
        if not 1 <= connect_timeout_seconds <= 10:
            raise ValueError("Provider database connection timeout must be between 1 and 10 seconds.")
        self.database_url = database_url
        self.connect_timeout_seconds = connect_timeout_seconds

    def _connect(self, **kwargs):
        return psycopg.connect(
            self.database_url,
            connect_timeout=self.connect_timeout_seconds,
            **kwargs,
        )

    def accept(self, envelope, raw_body: bytes, accepted_at: datetime) -> str:
        execution_id, workflow_id = _validate_started_event(envelope)
        event_id = envelope["event_id"]
        digest = hashlib.sha256(raw_body).hexdigest()
        callback_event_id = str(uuid5(CALLBACK_NAMESPACE, event_id))
        with self._connect(row_factory=dict_row) as connection:
            inserted = connection.execute(
                """
                INSERT INTO n8n_demo_events (
                    event_id, correlation_id, workflow_id, body_sha256,
                    callback_event_id, callback_occurred_at, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING RETURNING event_id
                """,
                (event_id, execution_id, workflow_id, digest, callback_event_id,
                 accepted_at, accepted_at, accepted_at),
            ).fetchone()
            if inserted is not None:
                return "accepted"
            existing = connection.execute(
                "SELECT body_sha256 FROM n8n_demo_events WHERE event_id = %s",
                (event_id,),
            ).fetchone()
            if existing is None or existing["body_sha256"] != digest:
                raise ValueError("Webhook event ID was already used for different content.")
            return "duplicate"

    def claim(self, claimed_at: datetime, lease_seconds: int, max_attempts: int):
        lease_expires_at = claimed_at + timedelta(seconds=lease_seconds)
        with self._connect(row_factory=dict_row) as connection:
            connection.execute(
                """
                UPDATE n8n_demo_events
                   SET status = 'dead', failure_code = 'retry_exhausted',
                       lease_expires_at = NULL, updated_at = %s
                 WHERE status = 'processing' AND lease_expires_at <= %s
                   AND attempt_count >= %s
                """,
                (claimed_at, claimed_at, max_attempts),
            )
            row = connection.execute(
                """
                WITH candidate AS (
                    SELECT event_id FROM n8n_demo_events
                     WHERE attempt_count < %s AND (
                         status = 'accepted'
                         OR (status = 'processing' AND lease_expires_at <= %s)
                     )
                     ORDER BY created_at, event_id
                     FOR UPDATE SKIP LOCKED LIMIT 1
                )
                UPDATE n8n_demo_events AS event
                   SET status = 'processing',
                       attempt_count = event.attempt_count + 1,
                       lease_expires_at = %s, updated_at = %s, failure_code = ''
                  FROM candidate
                 WHERE event.event_id = candidate.event_id
                RETURNING event.event_id::text
                """,
                (max_attempts, claimed_at, lease_expires_at, claimed_at),
            ).fetchone()
            return dict(row) if row is not None else None

    def synthetic_action(self, event_id: str, current_time: datetime) -> str | None:
        with self._connect(row_factory=dict_row) as connection:
            row = connection.execute(
                """
                SELECT event.workflow_id, event.result_status,
                       execution.status AS execution_status
                  FROM n8n_demo_events AS event
                  JOIN workflow_executions AS execution
                    ON execution.execution_id = event.correlation_id
                   AND execution.workflow_id = event.workflow_id
                   AND (execution.trigger_type = 'schedule' OR (execution.trigger_type = 'manual' AND EXISTS (SELECT 1 FROM webhook_deliveries outbox WHERE outbox.correlation_id = execution.execution_id AND outbox.direction = 'outbound' AND outbox.event_type = 'workflow.execution.started')))
                 WHERE event.event_id = %s AND event.status = 'processing'
                   AND event.lease_expires_at > %s
                   AND EXISTS (
                       SELECT 1
                        WHERE execution.status = 'running'
                           OR (event.result_status IS NOT NULL
                               AND execution.status = event.result_status)
                   )
                """,
                (event_id, current_time),
            ).fetchone()
        if row is None:
            return None
        if row["result_status"] is not None:
            return row["result_status"]
        return "failed" if row["workflow_id"] == "WF-N8N-DEMO-FAIL" else "completed"

    def prepare_outcome(
        self, event_id: str, result_status: str, current_time: datetime,
    ) -> dict[str, Any] | None:
        if result_status not in ALLOWED_RESULTS:
            raise ValueError("Synthetic result status is invalid.")
        with self._connect(row_factory=dict_row) as connection:
            row = connection.execute(
                """
                UPDATE n8n_demo_events
                   SET result_status = COALESCE(result_status, %s),
                       outcome_attempt = attempt_count, updated_at = %s
                 WHERE event_id = %s AND status = 'processing'
                   AND lease_expires_at > %s
                   AND outcome_attempt < attempt_count
                   AND (result_status IS NULL OR result_status = %s)
                   AND EXISTS (
                       SELECT 1 FROM workflow_executions AS execution
                        WHERE execution.execution_id = n8n_demo_events.correlation_id
                          AND execution.workflow_id = n8n_demo_events.workflow_id
                          AND (execution.trigger_type = 'schedule' OR (execution.trigger_type = 'manual' AND EXISTS (SELECT 1 FROM webhook_deliveries outbox WHERE outbox.correlation_id = execution.execution_id AND outbox.direction = 'outbound' AND outbox.event_type = 'workflow.execution.started')))
                          AND (
                              execution.status = 'running'
                              OR (n8n_demo_events.result_status IS NOT NULL
                                  AND execution.status = n8n_demo_events.result_status)
                          )
                   )
                RETURNING event_id::text, correlation_id, workflow_id,
                          callback_event_id::text, callback_occurred_at,
                          result_status
                """,
                (result_status, current_time, event_id, current_time, result_status),
            ).fetchone()
            return dict(row) if row is not None else None

    def record_callback_attempt(self, event_id: str, recorded_at: datetime) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE n8n_demo_events
                   SET callback_attempt_count = callback_attempt_count + 1,
                       updated_at = %s
                 WHERE event_id = %s AND status = 'processing'
                """,
                (recorded_at, event_id),
            )

    def record_callback_failure(self, event_id: str, recorded_at: datetime) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE n8n_demo_events
                   SET failure_code = 'callback_unavailable', updated_at = %s
                 WHERE event_id = %s AND status = 'processing'
                """,
                (recorded_at, event_id),
            )

    def complete_outcome(
        self, event_id: str, result_status: str, completed_at: datetime,
    ) -> bool:
        with self._connect(row_factory=dict_row) as connection:
            row = connection.execute(
                """
                UPDATE n8n_demo_events
                   SET status = 'completed', lease_expires_at = NULL,
                       completed_at = %s, updated_at = %s, failure_code = ''
                 WHERE event_id = %s AND result_status = %s
                   AND status = 'processing' AND outcome_attempt = attempt_count
                RETURNING event_id
                """,
                (completed_at, completed_at, event_id, result_status),
            ).fetchone()
            return row is not None


class N8nDemoServer(ThreadingHTTPServer):
    """Inject dependencies without placing secrets in request handlers."""

    def __init__(
        self, address, store: N8nDemoEventStore, internal_token: str,
        outbound_secret: str, inbound_secret: str, callback_url: str,
        signature_ttl_seconds: int = 300, lease_seconds: int = 30,
        max_attempts: int = 3, callback_max_attempts: int = 3,
        callback_timeout_seconds: float = 3,
        callback_retry_wait_seconds: float = 1,
        clock: Callable[[], datetime] = _utc_now,
        callback_sender: Callable = _send_callback_once,
        sleeper: Callable[[float], None] = time.sleep,
    ):
        if (
            callback_max_attempts <= 0
            or callback_timeout_seconds <= 0
            or callback_retry_wait_seconds < 0
        ):
            raise ValueError("Callback delivery settings must be bounded and positive.")
        super().__init__(address, DemoActionHandler)
        self.store = store
        self.internal_token = internal_token
        self.outbound_secret = outbound_secret
        self.inbound_secret = inbound_secret
        self.callback_url = callback_url
        self.signature_ttl_seconds = signature_ttl_seconds
        self.lease_seconds = lease_seconds
        self.max_attempts = max_attempts
        self.callback_max_attempts = callback_max_attempts
        self.callback_timeout_seconds = callback_timeout_seconds
        self.callback_retry_wait_seconds = callback_retry_wait_seconds
        self.clock = clock
        self.callback_sender = callback_sender
        self.sleeper = sleeper


class DemoActionHandler(BaseHTTPRequestHandler):
    """Expose only narrow authenticated synthetic operations."""

    server: N8nDemoServer

    def _json_response(self, status: HTTPStatus, value: dict[str, Any]) -> None:
        encoded = json.dumps(value, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def _authorized(self) -> bool:
        supplied = self.headers.get("Authorization", "")
        expected = f"Bearer {self.server.internal_token}"
        return hmac.compare_digest(supplied, expected)

    def _request_json(self) -> dict[str, Any]:
        try:
            content_length = int(self.headers.get("Content-Length", ""))
        except ValueError as error:
            raise ValueError("Invalid request length.") from error
        if (self.headers.get_content_type() != "application/json"
                or not 0 < content_length <= MAX_REQUEST_BYTES * 2):
            raise ValueError("Invalid request boundary.")
        try:
            value = json.loads(self.rfile.read(content_length))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("Invalid request JSON.") from error
        if not isinstance(value, dict):
            raise ValueError("Invalid request shape.")
        return value

    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_POST(self) -> None:
        if self.path not in {"/accept", "/claim", "/demo-action", "/outcome"}:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not self._authorized():
            self._json_response(HTTPStatus.UNAUTHORIZED, {"status": "rejected"})
            return
        try:
            request = self._request_json()
            if self.path == "/accept":
                self._accept(request)
            elif self.path == "/claim":
                self._claim(request)
            elif self.path == "/demo-action":
                self._demo_action(request)
            else:
                self._outcome(request)
        except (ValueError, binascii.Error, TypeError):
            self._json_response(HTTPStatus.BAD_REQUEST, {"status": "rejected"})
        except psycopg.Error:
            self._json_response(HTTPStatus.SERVICE_UNAVAILABLE, {"status": "unavailable"})

    def _accept(self, request: dict[str, Any]) -> None:
        if set(request) != {"raw_body_base64", "content_type", "timestamp", "event_id", "signature"}:
            raise ValueError("Invalid acceptance shape.")
        raw_body = base64.b64decode(request["raw_body_base64"], validate=True)
        envelope = verify_inbound_webhook(
            {"content_type": request["content_type"], "timestamp": request["timestamp"],
             "event_id": request["event_id"], "signature": request["signature"]},
            raw_body, self.server.outbound_secret, self.server.clock(),
            self.server.signature_ttl_seconds, MAX_REQUEST_BYTES,
        )
        _validate_started_event(envelope)
        status = self.server.store.accept(envelope, raw_body, self.server.clock())
        code = HTTPStatus.ACCEPTED if status == "accepted" else HTTPStatus.OK
        self._json_response(code, {"status": status, "event_id": envelope["event_id"]})

    def _claim(self, request: dict[str, Any]) -> None:
        if request:
            raise ValueError("Claim request must be empty.")
        event = self.server.store.claim(
            self.server.clock(), self.server.lease_seconds, self.server.max_attempts,
        )
        if event is None:
            self._json_response(HTTPStatus.OK, {"claimed": False})
            return
        self._json_response(HTTPStatus.OK, {"claimed": True, "event_id": event["event_id"]})

    def _demo_action(self, request: dict[str, Any]) -> None:
        if set(request) != {"event_id"}:
            raise ValueError("Invalid synthetic action shape.")
        event_id = _canonical_uuid(request["event_id"])
        status = self.server.store.synthetic_action(event_id, self.server.clock())
        if status is None:
            raise ValueError("Event is not currently owned by this worker lease.")
        self._json_response(HTTPStatus.OK, {"status": status})

    def _outcome(self, request: dict[str, Any]) -> None:
        if set(request) != {"event_id", "result_status"}:
            raise ValueError("Invalid outcome shape.")
        event_id = _canonical_uuid(request["event_id"])
        if request["result_status"] not in ALLOWED_RESULTS:
            raise ValueError("Synthetic result status is invalid.")
        event = self.server.store.prepare_outcome(
            event_id, request["result_status"], self.server.clock(),
        )
        if event is None:
            raise ValueError("Event cannot accept this outcome.")
        callback = build_webhook_envelope(
            event["callback_event_id"], event["correlation_id"],
            "workflow.execution.result", event["callback_occurred_at"],
            {"status": event["result_status"]},
        )
        delivered = False
        for attempt in range(self.server.callback_max_attempts):
            now = self.server.clock()
            headers, body = signed_webhook_headers(
                self.server.inbound_secret, callback, int(now.timestamp()),
            )
            self.server.store.record_callback_attempt(event_id, now)
            try:
                status = self.server.callback_sender(
                    self.server.callback_url, headers, body,
                    self.server.callback_timeout_seconds,
                )
                delivered = 200 <= status < 300
            except (OSError, TimeoutError):
                delivered = False
            if delivered:
                break
            if attempt + 1 < self.server.callback_max_attempts:
                self.server.sleeper(self.server.callback_retry_wait_seconds)
        if not delivered:
            self.server.store.record_callback_failure(event_id, self.server.clock())
            self._json_response(HTTPStatus.SERVICE_UNAVAILABLE, {"status": "unavailable"})
            return
        if not self.server.store.complete_outcome(
            event_id, event["result_status"], self.server.clock(),
        ):
            self._json_response(HTTPStatus.SERVICE_UNAVAILABLE, {"status": "unavailable"})
            return
        self._json_response(HTTPStatus.OK, {"status": "completed"})

    def log_message(self, _format: str, *_args: object) -> None:
        """Never emit request paths, headers, identifiers, or payloads."""


def main() -> None:
    server = N8nDemoServer(
        ("0.0.0.0", 8090),
        N8nDemoEventStore(_require_environment("DATABASE_URL")),
        _read_secret_file(PROVIDER_TOKEN_FILE, 32),
        _require_environment("ABAP_OUTBOUND_WEBHOOK_SECRET", 32),
        _require_environment("ABAP_INBOUND_WEBHOOK_SECRET", 32),
        _validate_callback_url(_require_environment("ABAP_CALLBACK_URL")),
        signature_ttl_seconds=int(os.environ.get("ABAP_WEBHOOK_SIGNATURE_TTL_SECONDS", "300")),
        lease_seconds=int(os.environ.get("ABAP_N8N_DEMO_LEASE_SECONDS", "30")),
        max_attempts=int(os.environ.get("ABAP_N8N_DEMO_MAX_ATTEMPTS", "3")),
        callback_max_attempts=int(os.environ.get("ABAP_N8N_CALLBACK_MAX_ATTEMPTS", "3")),
        callback_timeout_seconds=float(os.environ.get("ABAP_N8N_CALLBACK_TIMEOUT_SECONDS", "3")),
        callback_retry_wait_seconds=float(os.environ.get("ABAP_N8N_CALLBACK_RETRY_WAIT_SECONDS", "1")),
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
