import socket
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from database import (
    claim_due_outbound_webhook_deliveries,
    load_user_account_by_username,
    load_webhook_deliveries,
    insert_workflow,
    insert_workflow_execution,
)
from integration_config import load_integration_settings
from user_service import register_user_account
from webhook_contract import build_webhook_envelope
from webhook_delivery_service import prepare_outbound_webhook_delivery
from webhook_retry_worker import (
    reconstruct_workflow_execution_webhook,
    run_webhook_retry_cycle,
    webhook_retry_worker_is_ready,
)


NOW = datetime(2026, 9, 22, 9, 0, tzinfo=timezone.utc)


def settings(**overrides):
    values = {
        "ABAP_INTEGRATIONS_ENABLED": "true",
        "ABAP_N8N_BASE_URL": "https://automation.example.test",
        "ABAP_N8N_WORKFLOW_PATH": "/webhook/v1/workflow",
        "ABAP_INTEGRATION_ALLOWED_HOSTS": "automation.example.test",
        "ABAP_OUTBOUND_WEBHOOK_SECRET": "outbound-webhook-test-secret-1234567890",
        "ABAP_INBOUND_WEBHOOK_SECRET": "inbound-webhook-test-secret-1234567890",
        "ABAP_WEBHOOK_MAX_ATTEMPTS": "2",
        "ABAP_WEBHOOK_RETRY_LEASE_SECONDS": "30",
    }
    values.update(overrides)
    return load_integration_settings(values)


def public_resolver(_host, port, **_kwargs):
    return [
        (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port)),
    ]


class FakeResponse:
    def __init__(self, status):
        self.status = status

    def read(self, _amount=-1):
        return b""


class FakeConnection:
    def __init__(self, status):
        self.response = FakeResponse(status)
        self.requests = []
        self.closed = False

    def request(self, method, url, body, headers):
        self.requests.append((method, url, body, headers))

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


class TestWebhookRetryWorker(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database_file = Path(directory.name) / "webhook-retry.db"
        register_user_account("admin", "SecurePassword123!", "admin", self.database_file)
        self.admin = load_user_account_by_username("admin", self.database_file)
        self.assertIsNotNone(self.admin)
        if self.admin is None:
            self.fail("Test administrator could not be created.")
        self.assertTrue(insert_workflow(
            {
                "workflow_id": "WF-RETRY",
                "name": "Retry workflow",
                "description": "",
                "status": "active",
                "created_by_user_id": self.admin["user_id"],
                "created_at": NOW.isoformat(),
                "updated_at": NOW.isoformat(),
            },
            self.database_file,
        ))

    def create_execution(self, status="completed"):
        execution_id = f"WFE-{uuid4().hex.upper()}"
        self.assertTrue(insert_workflow_execution(
            {
                "execution_id": execution_id,
                "workflow_id": "WF-RETRY",
                "workflow_name": "Retry workflow",
                "trigger_type": "manual",
                "schedule_occurrence_id": None,
                "status": status,
                "started_by_user_id": self.admin["user_id"],
                "started_at": NOW.isoformat(),
                "finished_at": NOW.isoformat(),
                "result_summary": "Private result that must not be sent.",
            },
            self.database_file,
        ))
        return execution_id

    def queue_execution_delivery(self, execution_id, status="completed"):
        event_type = f"workflow.execution.{status}"
        envelope = build_webhook_envelope(
            str(uuid4()), execution_id, event_type, NOW,
            {"private_note": "must not be persisted or reconstructed"},
        )
        delivery_id = prepare_outbound_webhook_delivery(
            envelope,
            NOW,
            self.database_file,
        )
        self.assertIsNotNone(delivery_id)
        return delivery_id

    @staticmethod
    def connection_factory(connections):
        def create(*_args):
            return connections.pop(0)
        return create

    def test_restart_recovers_expired_lease_and_reconstructs_safe_execution_event(self):
        execution_id = self.create_execution()
        self.queue_execution_delivery(execution_id)
        connection = FakeConnection(202)

        leased = claim_due_outbound_webhook_deliveries(
            NOW.isoformat(),
            (NOW + timedelta(seconds=30)).isoformat(),
            1,
            self.database_file,
        )
        self.assertEqual(len(leased), 1)
        before_lease_expires = run_webhook_retry_cycle(
            NOW + timedelta(seconds=29),
            settings(),
            self.database_file,
            public_resolver,
            self.connection_factory([]),
        )
        self.assertEqual(before_lease_expires["claimed"], 0)

        restarted = run_webhook_retry_cycle(
            NOW + timedelta(seconds=31),
            settings(),
            self.database_file,
            public_resolver,
            self.connection_factory([connection]),
        )
        self.assertEqual(restarted, {"claimed": 1, "succeeded": 1, "retrying": 0, "failed": 0})
        delivery = load_webhook_deliveries(database_file=self.database_file)[0]
        self.assertEqual(delivery["status"], "succeeded")
        self.assertEqual(delivery["attempt_count"], 1)
        sent_body = connection.requests[0][2].decode("utf-8")
        self.assertIn(execution_id, sent_body)
        self.assertNotIn("private_note", sent_body)
        self.assertNotIn("Private result", sent_body)

        after_success = run_webhook_retry_cycle(
            NOW + timedelta(minutes=1),
            settings(),
            self.database_file,
            public_resolver,
            self.connection_factory([]),
        )
        self.assertEqual(after_success["claimed"], 0)

    def test_retryable_failure_is_rescheduled_then_terminal_after_max_attempts(self):
        execution_id = self.create_execution()
        self.queue_execution_delivery(execution_id)
        first = run_webhook_retry_cycle(
            NOW, settings(), self.database_file, public_resolver,
            self.connection_factory([FakeConnection(503)]),
        )
        self.assertEqual(first["retrying"], 1)
        delivery = load_webhook_deliveries(database_file=self.database_file)[0]
        self.assertEqual((delivery["status"], delivery["attempt_count"]), ("retrying", 1))

        second = run_webhook_retry_cycle(
            NOW + timedelta(milliseconds=500), settings(), self.database_file,
            public_resolver, self.connection_factory([]),
        )
        self.assertEqual(second["claimed"], 0)

        final = run_webhook_retry_cycle(
            NOW + timedelta(seconds=1), settings(), self.database_file,
            public_resolver, self.connection_factory([FakeConnection(503)]),
        )
        self.assertEqual(final["failed"], 1)
        delivery = load_webhook_deliveries(database_file=self.database_file)[0]
        self.assertEqual((delivery["status"], delivery["attempt_count"]), ("failed", 2))

    def test_unknown_or_changed_delivery_source_fails_without_sending(self):
        self.queue_execution_delivery("WFE-MISSING")
        result = run_webhook_retry_cycle(
            NOW, settings(), self.database_file, public_resolver,
            lambda *_args: self.fail("an unreconstructable event must not send"),
        )
        delivery = load_webhook_deliveries(database_file=self.database_file)[0]
        self.assertEqual(result["failed"], 1)
        self.assertEqual(delivery["failure_code"], "reconstruction_unavailable")

    def test_concurrent_cycles_lease_one_delivery_to_one_sender(self):
        execution_id = self.create_execution()
        self.queue_execution_delivery(execution_id)
        connection = FakeConnection(202)

        with ThreadPoolExecutor(max_workers=2) as workers:
            outcomes = list(workers.map(
                lambda _value: run_webhook_retry_cycle(
                    NOW,
                    settings(),
                    self.database_file,
                    public_resolver,
                    self.connection_factory([connection]),
                ),
                range(2),
            ))

        self.assertEqual(sum(item["claimed"] for item in outcomes), 1)
        self.assertEqual(len(connection.requests), 1)
        delivery = load_webhook_deliveries(database_file=self.database_file)[0]
        self.assertEqual((delivery["status"], delivery["attempt_count"]), ("succeeded", 1))

    def test_reconstruction_requires_matching_terminal_execution_status(self):
        execution_id = self.create_execution("failed")
        delivery_id = self.queue_execution_delivery(execution_id, "completed")
        delivery = load_webhook_deliveries(database_file=self.database_file)[0]
        self.assertEqual(delivery["delivery_id"], delivery_id)
        self.assertIsNone(
            reconstruct_workflow_execution_webhook(delivery, self.database_file),
        )

    def test_readiness_requires_enabled_integration_and_usable_database(self):
        self.assertTrue(
            webhook_retry_worker_is_ready(
                self.database_file,
                lambda: settings(),
            )
        )
        self.assertFalse(
            webhook_retry_worker_is_ready(
                self.database_file,
                lambda: load_integration_settings({}),
            )
        )


if __name__ == "__main__":
    unittest.main()
