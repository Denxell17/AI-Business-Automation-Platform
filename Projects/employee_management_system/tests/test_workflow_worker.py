import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

import psycopg

from database import (
    load_user_account_by_username,
    load_workflow_executions,
    load_workflow_task_executions,
)
from user_service import register_user_account
from worker_config import load_worker_settings
from workflow_service import (
    create_workflow,
    create_workflow_schedule,
    create_workflow_task,
    update_workflow,
)
from workflow_worker import run_worker_cycle, run_worker_forever
from integration_config import load_integration_settings


TEST_DATABASE_URL = os.environ.get("ABAP_TEST_DATABASE_URL", "").strip()


class TestWorkflowWorker(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database_file = Path(directory.name) / "worker.db"
        register_user_account(
            "admin", "SecurePassword123!", "admin", self.database_file,
        )
        self.admin = load_user_account_by_username("admin", self.database_file)
        self.assertTrue(create_workflow(
            self.admin, "WF-WORKER", "Worker workflow", "", "draft",
            self.database_file,
        ))
        self.assertTrue(create_workflow_task(
            self.admin, "TASK-WORKER", "WF-WORKER", 1, "Review request", "",
            "manual", True, self.database_file,
        ))
        self.assertTrue(update_workflow(
            self.admin, "WF-WORKER", "Worker workflow", "", "active",
            self.database_file,
        ))
        self.settings = load_worker_settings(
            {
                "ABAP_WORKER_ENABLED": "true",
                "ABAP_WORKER_POLL_SECONDS": "1",
                "ABAP_WORKER_CLAIM_LIMIT": "10",
                "ABAP_WORKER_MAX_ATTEMPTS": "2",
                "ABAP_WORKER_RETRY_BASE_SECONDS": "2",
                "ABAP_WORKER_RETRY_MAX_SECONDS": "8",
                "ABAP_WORKER_STALE_AFTER_SECONDS": "60",
                "ABAP_WORKER_SHUTDOWN_GRACE_SECONDS": "1",
            }
        )

    def create_schedule(self, is_enabled=True):
        self.assertTrue(create_workflow_schedule(
            self.admin, "SCH-WORKER", "WF-WORKER", "daily", "09:30", "",
            is_enabled, self.database_file,
        ))

    def now(self):
        return datetime(2026, 9, 8, 1, 31, tzinfo=timezone.utc)

    def test_due_schedule_creates_one_scheduled_execution_and_task_snapshot(self):
        self.create_schedule()

        result = run_worker_cycle(self.now(), self.settings, self.database_file)

        executions = load_workflow_executions("WF-WORKER", self.database_file)
        self.assertEqual(result, {
            "claimed": 1, "started": 1, "recovered": 0, "failed": 0,
        })
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]["trigger_type"], "schedule")
        self.assertIsNotNone(executions[0]["schedule_occurrence_id"])
        self.assertIsNone(executions[0]["started_by_user_id"])
        task_runs = load_workflow_task_executions(
            executions[0]["execution_id"], self.database_file,
        )
        self.assertEqual(len(task_runs), 1)
        self.assertEqual(task_runs[0]["status"], "running")

    def test_early_disabled_and_inactive_schedules_do_not_start_runs(self):
        self.create_schedule(is_enabled=False)

        disabled = run_worker_cycle(self.now(), self.settings, self.database_file)
        early = run_worker_cycle(
            self.now() - timedelta(minutes=2), self.settings, self.database_file,
        )
        self.assertTrue(update_workflow(
            self.admin, "WF-WORKER", "Worker workflow", "", "inactive",
            self.database_file,
        ))
        inactive = run_worker_cycle(self.now(), self.settings, self.database_file)

        self.assertEqual(disabled["started"], 0)
        self.assertEqual(early["started"], 0)
        self.assertEqual(inactive["started"], 0)
        self.assertEqual(load_workflow_executions("WF-WORKER", self.database_file), [])

    def test_repeated_cycles_do_not_duplicate_a_claimed_occurrence(self):
        self.create_schedule()

        first = run_worker_cycle(self.now(), self.settings, self.database_file)
        second = run_worker_cycle(self.now(), self.settings, self.database_file)

        self.assertEqual(first["started"], 1)
        self.assertEqual(second["claimed"], 0)
        self.assertEqual(second["started"], 0)
        self.assertEqual(len(load_workflow_executions("WF-WORKER", self.database_file)), 1)

    def test_new_scheduled_execution_dispatches_only_a_minimal_started_event(self):
        self.create_schedule()
        integration = load_integration_settings({
            "ABAP_INTEGRATIONS_ENABLED": "true",
            "ABAP_N8N_BASE_URL": "https://automation.example.test",
            "ABAP_N8N_WORKFLOW_PATH": "/webhook/v1/workflow",
            "ABAP_INTEGRATION_ALLOWED_HOSTS": "automation.example.test",
            "ABAP_OUTBOUND_WEBHOOK_SECRET": "outbound-worker-test-secret",
            "ABAP_INBOUND_WEBHOOK_SECRET": "inbound-worker-test-secret",
        })
        with patch("workflow_worker.deliver_outbound_webhook") as deliver:
            deliver.return_value = {
                "sent": True, "duplicate": False, "delivery_id": "WHD-TEST",
                "attempts": 1,
            }
            result = run_worker_cycle(
                self.now(), self.settings, self.database_file,
                integration_settings_loader=lambda: integration,
            )

        envelope = deliver.call_args.args[1]
        self.assertEqual(result["started"], 1)
        self.assertEqual(envelope["event_type"], "workflow.execution.started")
        self.assertEqual(
            set(envelope["data"]),
            {"execution_id", "workflow_id", "trigger_type"},
        )
        self.assertEqual(envelope["data"]["trigger_type"], "schedule")

    def test_start_retry_uses_bounded_exponential_backoff(self):
        self.create_schedule()
        delays = []
        original_start = __import__(
            "workflow_worker",
        ).start_scheduled_workflow_execution
        calls = 0

        def temporarily_unavailable(*args, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                raise OSError("temporary database interruption")
            return original_start(*args, **kwargs)

        with patch(
            "workflow_worker.start_scheduled_workflow_execution",
            side_effect=temporarily_unavailable,
        ):
            result = run_worker_cycle(
                self.now(), self.settings, self.database_file, delays.append,
            )

        self.assertEqual(result["started"], 1)
        self.assertEqual(delays, [2])

    def test_stale_scheduled_run_is_failed_with_its_running_task(self):
        self.create_schedule()
        run_worker_cycle(self.now(), self.settings, self.database_file)
        stale_settings = dict(self.settings)
        stale_settings["stale_after_seconds"] = 60

        result = run_worker_cycle(
            self.now() + timedelta(seconds=61), stale_settings, self.database_file,
        )

        execution = load_workflow_executions("WF-WORKER", self.database_file)[0]
        task_run = load_workflow_task_executions(
            execution["execution_id"], self.database_file,
        )[0]
        self.assertEqual(result["recovered"], 1)
        self.assertEqual(execution["status"], "failed")
        self.assertEqual(task_run["status"], "failed")

    def test_disabled_worker_and_pre_stopped_loop_do_not_process_work(self):
        self.create_schedule()
        disabled_settings = dict(self.settings)
        disabled_settings["enabled"] = False
        stop_event = threading.Event()
        stop_event.set()

        result = run_worker_cycle(self.now(), disabled_settings, self.database_file)
        run_worker_forever(self.settings, self.database_file, stop_event)

        self.assertEqual(result["started"], 0)
        self.assertEqual(load_workflow_executions("WF-WORKER", self.database_file), [])

    def test_shutdown_interrupts_retry_backoff_without_creating_a_run(self):
        self.create_schedule()
        class ShutdownDuringBackoff:
            requested = False

            def is_set(self):
                return self.requested

            def wait(self, _delay):
                self.requested = True
                return True

        stop_event = ShutdownDuringBackoff()

        with patch(
            "workflow_worker.start_scheduled_workflow_execution",
            side_effect=OSError("temporary database interruption"),
        ):
            result = run_worker_cycle(
                self.now(), self.settings, self.database_file,
                lambda _delay: self.fail("shutdown should use its event wait"),
                stop_event,
            )

        self.assertEqual(result["started"], 0)
        self.assertEqual(result["failed"], 0)
        self.assertEqual(load_workflow_executions("WF-WORKER", self.database_file), [])


class TestWorkerConfiguration(unittest.TestCase):
    def test_rejects_invalid_retry_window_and_boolean(self):
        with self.assertRaises(ValueError):
            load_worker_settings({"ABAP_WORKER_ENABLED": "sometimes"})
        with self.assertRaises(ValueError):
            load_worker_settings(
                {
                    "ABAP_WORKER_RETRY_BASE_SECONDS": "10",
                    "ABAP_WORKER_RETRY_MAX_SECONDS": "5",
                }
            )


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "ABAP_TEST_DATABASE_URL is required for live PostgreSQL worker tests.",
)
class TestPostgresqlWorkflowWorkerConcurrency(unittest.TestCase):
    def setUp(self):
        self.identifier = uuid4().hex.upper()
        self.workflow_id = f"WF-PG-WORKER-{self.identifier}"
        self.task_id = f"TASK-PG-WORKER-{self.identifier}"
        self.schedule_id = f"SCH-PG-WORKER-{self.identifier}"
        self.username = f"pg_worker_{self.identifier.casefold()}"
        self.environment = patch.dict(
            os.environ,
            {
                "DATABASE_BACKEND": "postgresql",
                "DATABASE_URL": TEST_DATABASE_URL,
            },
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        register_user_account(
            self.username, "SecurePassword123!", "admin",
        )
        self.admin = load_user_account_by_username(self.username)
        self.assertTrue(create_workflow(
            self.admin, self.workflow_id, "PostgreSQL worker", "", "draft",
        ))
        self.assertTrue(create_workflow_task(
            self.admin, self.task_id, self.workflow_id, 1, "Review request", "",
            "manual", True,
        ))
        self.assertTrue(update_workflow(
            self.admin, self.workflow_id, "PostgreSQL worker", "", "active",
        ))
        self.assertTrue(create_workflow_schedule(
            self.admin, self.schedule_id, self.workflow_id, "daily", "09:30", "",
            True,
        ))
        self.settings = load_worker_settings(
            {"ABAP_WORKER_ENABLED": "true", "ABAP_WORKER_CLAIM_LIMIT": "10"}
        )

    def tearDown(self):
        with psycopg.connect(TEST_DATABASE_URL) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """DELETE FROM workflow_task_executions
                       WHERE execution_id IN (
                           SELECT execution_id FROM workflow_executions
                           WHERE workflow_id = %s
                       )""",
                    (self.workflow_id,),
                )
                cursor.execute(
                    "DELETE FROM workflow_executions WHERE workflow_id = %s",
                    (self.workflow_id,),
                )
                cursor.execute(
                    "DELETE FROM workflow_schedule_occurrences WHERE workflow_id = %s",
                    (self.workflow_id,),
                )
                cursor.execute(
                    "DELETE FROM workflow_schedules WHERE workflow_id = %s",
                    (self.workflow_id,),
                )
                cursor.execute(
                    "DELETE FROM workflow_tasks WHERE workflow_id = %s",
                    (self.workflow_id,),
                )
                cursor.execute(
                    "DELETE FROM workflows WHERE workflow_id = %s",
                    (self.workflow_id,),
                )
                cursor.execute("DELETE FROM users WHERE username = %s", (self.username,))

    def test_concurrent_workers_create_one_scheduled_execution(self):
        current_time = datetime(2026, 9, 8, 1, 31, tzinfo=timezone.utc)

        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(
                lambda _value: run_worker_cycle(current_time, self.settings),
                range(2),
            ))

        executions = load_workflow_executions(self.workflow_id)
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0]["trigger_type"], "schedule")
        self.assertEqual(sum(result["started"] for result in results), 1)


if __name__ == "__main__":
    unittest.main()
