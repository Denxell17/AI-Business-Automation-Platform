"""Separate, duplicate-safe worker for scheduled ABAP workflow runs."""

import argparse
import logging
import signal
import sqlite3
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from uuid import uuid4

import psycopg

from database import (
    DATABASE_FILE,
    fail_stale_scheduled_workflow_execution,
    load_stale_scheduled_workflow_executions,
    load_unstarted_workflow_schedule_occurrences,
    workflow_schedule_occurrence_is_started,
)
from integration_config import IntegrationSettings, load_integration_settings
from schedule_service import claim_due_workflow_schedules
from system_status_service import database_is_ready
from webhook_contract import build_webhook_envelope
from webhook_sender import deliver_outbound_webhook
from worker_config import WorkerSettings, load_worker_settings
from workflow_service import start_scheduled_workflow_execution


worker_logger = logging.getLogger("abap.worker")


def _utc_timestamp(current_time: datetime) -> str:
    if not isinstance(current_time, datetime) or current_time.tzinfo is None:
        raise ValueError("Worker time must include a time zone.")
    return current_time.astimezone(timezone.utc).isoformat()


def worker_is_ready(
    database_file: Path = DATABASE_FILE,
    settings_loader: Callable[[], WorkerSettings] = load_worker_settings,
) -> bool | None:
    """Report only safe readiness information for the worker process."""
    try:
        settings = settings_loader()
    except ValueError:
        return False
    return settings["enabled"] and database_is_ready(database_file)


def recover_stale_scheduled_executions(
    current_time: datetime,
    settings: WorkerSettings,
    database_file: Path = DATABASE_FILE,
) -> int:
    """Terminally fail scheduled runs that exceeded the recovery threshold."""
    now = _utc_timestamp(current_time)
    stale_before = (
        current_time.astimezone(timezone.utc)
        - timedelta(seconds=settings["stale_after_seconds"])
    ).isoformat()
    recovered = 0
    for execution in load_stale_scheduled_workflow_executions(
        stale_before, database_file,
    ):
        if fail_stale_scheduled_workflow_execution(
            execution["execution_id"],
            stale_before,
            now,
            "Scheduled execution exceeded the worker recovery limit.",
            database_file,
        ):
            recovered += 1
            worker_logger.warning(
                "event=scheduled_execution_recovered execution_id=%s",
                execution["execution_id"],
            )
    return recovered


def dispatch_scheduled_execution_to_integration(
    execution: dict[str, object],
    current_time: datetime,
    settings: IntegrationSettings,
    database_file: Path = DATABASE_FILE,
) -> bool:
    """Send only a new scheduled run's fixed, non-private dispatch envelope."""
    if not settings["enabled"]:
        return False
    execution_id = execution.get("execution_id")
    workflow_id = execution.get("workflow_id")
    if not isinstance(execution_id, str) or not isinstance(workflow_id, str):
        return False
    try:
        envelope = build_webhook_envelope(
            str(uuid4()),
            execution_id,
            "workflow.execution.started",
            current_time,
            {
                "execution_id": execution_id,
                "workflow_id": workflow_id,
                "trigger_type": "schedule",
            },
        )
        result = deliver_outbound_webhook(
            settings, envelope, current_time, database_file,
        )
    except (OSError, ValueError, sqlite3.Error, psycopg.Error):
        worker_logger.error(
            "event=scheduled_execution_dispatch_failed execution_id=%s",
            execution_id,
        )
        return False
    worker_logger.info(
        "event=scheduled_execution_dispatched execution_id=%s sent=%s attempts=%s",
        execution_id, result["sent"], result["attempts"],
    )
    return result["sent"]


def _start_occurrence_with_retry(
    occurrence: dict[str, str],
    current_time: datetime,
    settings: WorkerSettings,
    database_file: Path,
    sleep: Callable[[float], None],
    stop_event: threading.Event | None = None,
    dispatch: Callable[[dict[str, object]], None] | None = None,
) -> bool | None:
    """Retry only durable, idempotent scheduled-run creation."""
    for attempt in range(settings["max_attempts"]):
        if stop_event is not None and stop_event.is_set():
            return None
        try:
            execution = start_scheduled_workflow_execution(
                occurrence, _utc_timestamp(current_time), database_file,
            )
        except (OSError, sqlite3.Error, psycopg.Error):
            execution = None
        if execution is not None:
            worker_logger.info(
                "event=scheduled_execution_started occurrence_id=%s execution_id=%s",
                occurrence["occurrence_id"], execution["execution_id"],
            )
            if dispatch is not None:
                dispatch(execution)
            return True
        if workflow_schedule_occurrence_is_started(
            occurrence["occurrence_id"], database_file,
        ):
            return None
        if attempt + 1 < settings["max_attempts"]:
            delay = min(
                settings["retry_base_seconds"] * (2 ** attempt),
                settings["retry_max_seconds"],
            )
            if stop_event is not None:
                if stop_event.wait(delay):
                    return None
            else:
                sleep(delay)
    worker_logger.error(
        "event=scheduled_execution_start_failed occurrence_id=%s attempts=%s",
        occurrence["occurrence_id"], settings["max_attempts"],
    )
    return False


def run_worker_cycle(
    current_time: datetime,
    settings: WorkerSettings,
    database_file: Path = DATABASE_FILE,
    sleep: Callable[[float], None] = time.sleep,
    stop_event: threading.Event | None = None,
    integration_settings_loader: Callable[[], IntegrationSettings] = load_integration_settings,
) -> dict[str, int]:
    """Recover stale runs, claim due work, and start pending occurrences once."""
    _utc_timestamp(current_time)
    if not settings["enabled"] or (stop_event is not None and stop_event.is_set()):
        return {"claimed": 0, "started": 0, "recovered": 0, "failed": 0}
    recovered = recover_stale_scheduled_executions(
        current_time, settings, database_file,
    )
    claimed = claim_due_workflow_schedules(current_time, database_file)
    pending = load_unstarted_workflow_schedule_occurrences(
        settings["claim_limit"], database_file,
    )
    dispatch = None
    try:
        integration_settings = integration_settings_loader()
    except ValueError:
        integration_settings = None
        worker_logger.error("event=scheduled_execution_dispatch_configuration_error")
    if integration_settings is not None and integration_settings["enabled"]:
        dispatch = lambda execution: dispatch_scheduled_execution_to_integration(
            execution, current_time, integration_settings, database_file,
        )
    started = 0
    failed = 0
    for occurrence in pending:
        outcome = _start_occurrence_with_retry(
            occurrence, current_time, settings, database_file, sleep, stop_event,
            dispatch,
        )
        if outcome is True:
            started += 1
        elif outcome is False:
            failed += 1
    return {
        "claimed": len(claimed),
        "started": started,
        "recovered": recovered,
        "failed": failed,
    }


def run_worker_forever(
    settings: WorkerSettings,
    database_file: Path = DATABASE_FILE,
    stop_event: threading.Event | None = None,
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> None:
    """Run isolated worker cycles until a graceful shutdown request arrives."""
    selected_stop_event = stop_event if stop_event is not None else threading.Event()
    while not selected_stop_event.is_set():
        run_worker_cycle(now(), settings, database_file, stop_event=selected_stop_event)
        selected_stop_event.wait(settings["poll_seconds"])


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    parser = argparse.ArgumentParser(description="Run the ABAP schedule worker.")
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    if arguments.check:
        return 0 if worker_is_ready() else 1
    try:
        settings = load_worker_settings()
    except ValueError:
        worker_logger.error("event=worker_configuration_error")
        return 1
    if not settings["enabled"] or not database_is_ready(DATABASE_FILE):
        worker_logger.error("event=worker_not_ready")
        return 1
    stop_event = threading.Event()
    signal.signal(signal.SIGINT, lambda *_args: stop_event.set())
    signal.signal(signal.SIGTERM, lambda *_args: stop_event.set())
    run_worker_forever(settings, stop_event=stop_event)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
