"""Restart-safe outbound webhook retries using metadata-only delivery records."""

import argparse
import logging
import signal
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

import psycopg

from database import (
    DATABASE_FILE,
    claim_due_outbound_webhook_deliveries,
    load_workflow_execution_by_id,
    record_outbound_webhook_attempt,
)
from integration_config import IntegrationSettings, load_integration_settings
from system_status_service import database_is_ready
from webhook_contract import WebhookEnvelope, build_webhook_envelope
from webhook_sender import next_webhook_attempt_at, send_outbound_webhook_once


retry_worker_logger = logging.getLogger("abap.webhook_retry_worker")

_WORKFLOW_EVENT_STATUSES = {
    "workflow.execution.started": "running",
    "workflow.execution.completed": "completed",
    "workflow.execution.failed": "failed",
}


def _timestamp(current_time: datetime) -> str:
    if not isinstance(current_time, datetime) or current_time.tzinfo is None:
        raise ValueError("Webhook retry worker time must include a time zone.")
    return current_time.astimezone(timezone.utc).isoformat()


def _delivery_time(value: str) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed


def reconstruct_workflow_execution_webhook(
    delivery: dict[str, object],
    database_file: Path = DATABASE_FILE,
) -> WebhookEnvelope | None:
    """Rebuild only an allowlisted event from its durable execution record."""
    expected_status = _WORKFLOW_EVENT_STATUSES.get(delivery.get("event_type"))
    correlation_id = delivery.get("correlation_id")
    event_id = delivery.get("event_id")
    occurred_at = _delivery_time(delivery.get("created_at"))
    if (
        expected_status is None
        or not isinstance(correlation_id, str)
        or not isinstance(event_id, str)
        or occurred_at is None
    ):
        return None
    execution = load_workflow_execution_by_id(correlation_id, database_file)
    if execution is None or execution["status"] != expected_status:
        return None
    return build_webhook_envelope(
        event_id,
        execution["execution_id"],
        delivery["event_type"],
        occurred_at,
        (
            {
                "execution_id": execution["execution_id"],
                "workflow_id": execution["workflow_id"],
                "trigger_type": execution["trigger_type"],
            }
            if delivery["event_type"] == "workflow.execution.started"
            else {
                "execution_id": execution["execution_id"],
                "workflow_id": execution["workflow_id"],
                "status": execution["status"],
                "trigger_type": execution["trigger_type"],
            }
        ),
    )


def webhook_retry_worker_is_ready(
    database_file: Path = DATABASE_FILE,
    settings_loader: Callable[[], IntegrationSettings] = load_integration_settings,
) -> bool:
    """Report readiness without exposing integration configuration values."""
    try:
        settings = settings_loader()
    except ValueError:
        return False
    return settings["enabled"] and database_is_ready(database_file)


def run_webhook_retry_cycle(
    current_time: datetime,
    settings: IntegrationSettings,
    database_file: Path = DATABASE_FILE,
    resolver: Callable[..., list[tuple]] | None = None,
    connection_factory: Callable[..., object] | None = None,
    stop_event: threading.Event | None = None,
) -> dict[str, int]:
    """Lease, reconstruct, and send due delivery attempts exactly once per lease."""
    now = _timestamp(current_time)
    if not settings["enabled"] or (stop_event is not None and stop_event.is_set()):
        return {"claimed": 0, "succeeded": 0, "retrying": 0, "failed": 0}
    lease_until = _timestamp(
        current_time.astimezone(timezone.utc)
        + timedelta(seconds=settings["retry_lease_seconds"]),
    )
    deliveries = claim_due_outbound_webhook_deliveries(
        now,
        lease_until,
        settings["retry_claim_limit"],
        database_file,
    )
    outcomes = {"claimed": len(deliveries), "succeeded": 0, "retrying": 0, "failed": 0}
    for delivery in deliveries:
        if stop_event is not None and stop_event.is_set():
            break
        envelope = reconstruct_workflow_execution_webhook(delivery, database_file)
        if envelope is None:
            if record_outbound_webhook_attempt(
                delivery["delivery_id"], "failed", now, None,
                "reconstruction_unavailable", None, database_file,
            ):
                outcomes["failed"] += 1
                retry_worker_logger.error(
                    "event=webhook_retry_reconstruction_failed delivery_id=%s",
                    delivery["delivery_id"],
                )
            continue
        attempt_number = delivery["attempt_count"] + 1
        kwargs = {}
        if resolver is not None:
            kwargs["resolver"] = resolver
        if connection_factory is not None:
            kwargs["connection_factory"] = connection_factory
        succeeded, retryable, response_status, failure_code = (
            send_outbound_webhook_once(settings, envelope, current_time, **kwargs)
        )
        if succeeded:
            status, next_attempt_at = "succeeded", None
            outcomes["succeeded"] += 1
        elif retryable and attempt_number < settings["max_attempts"]:
            status = "retrying"
            next_attempt_at = next_webhook_attempt_at(current_time, attempt_number)
            outcomes["retrying"] += 1
        else:
            status, next_attempt_at = "failed", None
            outcomes["failed"] += 1
        if record_outbound_webhook_attempt(
            delivery["delivery_id"], status, now, response_status,
            failure_code, next_attempt_at, database_file,
        ):
            retry_worker_logger.info(
                "event=webhook_retry_attempt delivery_id=%s status=%s attempt=%s",
                delivery["delivery_id"], status, attempt_number,
            )
    return outcomes


def run_webhook_retry_forever(
    settings: IntegrationSettings,
    database_file: Path = DATABASE_FILE,
    stop_event: threading.Event | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> None:
    """Continue retry cycles until a graceful shutdown is requested."""
    selected_stop_event = stop_event if stop_event is not None else threading.Event()
    while not selected_stop_event.is_set():
        try:
            run_webhook_retry_cycle(now(), settings, database_file, stop_event=selected_stop_event)
        except (OSError, sqlite3.Error, psycopg.Error, ValueError):
            retry_worker_logger.error("event=webhook_retry_cycle_failed")
        selected_stop_event.wait(settings["retry_poll_seconds"])


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    parser = argparse.ArgumentParser(description="Run the ABAP webhook retry worker.")
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    if arguments.check:
        return 0 if webhook_retry_worker_is_ready() else 1
    try:
        settings = load_integration_settings()
    except ValueError:
        retry_worker_logger.error("event=webhook_retry_configuration_error")
        return 1
    if not webhook_retry_worker_is_ready(settings_loader=lambda: settings):
        retry_worker_logger.error("event=webhook_retry_worker_not_ready")
        return 1
    stop_event = threading.Event()
    signal.signal(signal.SIGINT, lambda *_args: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_args: stop_event.set())
    run_webhook_retry_forever(settings, stop_event=stop_event)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
