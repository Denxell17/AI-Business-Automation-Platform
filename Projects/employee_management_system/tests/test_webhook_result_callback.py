import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi.testclient import TestClient

from database import (
    claim_workflow_schedule_occurrence,
    create_scheduled_workflow_execution,
    insert_workflow,
    insert_workflow_execution,
    insert_workflow_schedule,
    load_user_account_by_username,
    load_webhook_deliveries,
    load_workflow_execution_by_id,
    load_workflow_task_executions,
)
from integration_config import load_integration_settings
from user_service import register_user_account
from web_app import create_web_application
from webhook_contract import build_webhook_envelope, signed_webhook_headers


NOW = datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc)
INBOUND_SECRET = "inbound-result-test-secret-1234567890"


def settings():
    return load_integration_settings({
        "ABAP_INTEGRATIONS_ENABLED": "true",
        "ABAP_N8N_BASE_URL": "https://automation.example.test",
        "ABAP_N8N_WORKFLOW_PATH": "/webhook/v1/workflow",
        "ABAP_INTEGRATION_ALLOWED_HOSTS": "automation.example.test",
        "ABAP_OUTBOUND_WEBHOOK_SECRET": "outbound-result-test-secret-1234567890",
        "ABAP_INBOUND_WEBHOOK_SECRET": INBOUND_SECRET,
    })


class TestWebhookResultCallback(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database_file = Path(directory.name) / "webhook-results.db"
        register_user_account("admin", "SecurePassword123!", "admin", self.database_file)
        self.admin = load_user_account_by_username("admin", self.database_file)
        self.assertIsNotNone(self.admin)
        if self.admin is None:
            self.fail("Test administrator could not be created.")
        timestamp = NOW.isoformat()
        self.assertTrue(insert_workflow({
            "workflow_id": "WF-RESULT", "name": "Result workflow",
            "description": "", "status": "active",
            "created_by_user_id": self.admin["user_id"],
            "created_at": timestamp, "updated_at": timestamp,
        }, self.database_file))
        self.assertTrue(insert_workflow_schedule({
            "schedule_id": "SCH-RESULT", "workflow_id": "WF-RESULT",
            "schedule_type": "manual", "scheduled_time": None,
            "day_of_week": None, "is_enabled": True,
            "created_by_user_id": self.admin["user_id"],
            "created_at": timestamp, "updated_at": timestamp,
        }, self.database_file))
        self.application = create_web_application(
            database_file=self.database_file,
            session_secret="webhook-result-test-session-secret",
            integration_settings_loader=settings,
            webhook_clock=lambda: NOW,
        )
        self.client = TestClient(self.application)
        self.addCleanup(self.client.close)

    def scheduled_execution(self):
        execution_id = f"WFE-{uuid4().hex.upper()}"
        occurrence_id = f"OCC-{uuid4().hex.upper()}"
        self.assertTrue(claim_workflow_schedule_occurrence({
            "occurrence_id": occurrence_id,
            "schedule_id": "SCH-RESULT",
            "workflow_id": "WF-RESULT",
            "scheduled_for_utc": NOW.isoformat(),
            "claimed_at": NOW.isoformat(),
        }, self.database_file))
        self.assertTrue(create_scheduled_workflow_execution({
            "execution_id": execution_id,
            "workflow_id": "WF-RESULT",
            "workflow_name": "Result workflow",
            "trigger_type": "schedule",
            "schedule_occurrence_id": occurrence_id,
            "status": "running",
            "started_by_user_id": None,
            "started_at": NOW.isoformat(),
            "finished_at": None,
            "result_summary": "Scheduled execution started.",
        }, [{
            "task_execution_id": f"TASK-RUN-{uuid4().hex.upper()}",
            "execution_id": execution_id,
            "task_id": "TASK-RESULT",
            "sequence_number": 1,
            "task_title": "External action",
            "status": "running",
            "started_at": NOW.isoformat(),
            "finished_at": None,
            "result_summary": "Task execution started.",
        }], self.database_file))
        return execution_id

    def callback(self, execution_id, data):
        envelope = build_webhook_envelope(
            str(uuid4()), execution_id, "workflow.execution.result", NOW, data,
        )
        headers, body = signed_webhook_headers(
            INBOUND_SECRET, envelope, int(NOW.timestamp()),
        )
        response = self.client.post(
            "/integrations/webhooks/callback",
            content=body,
            headers={
                "Content-Type": headers["content_type"],
                "X-ABAP-Timestamp": headers["timestamp"],
                "X-ABAP-Event-Id": headers["event_id"],
                "X-ABAP-Signature": headers["signature"],
            },
        )
        return response, envelope

    def test_signed_result_finishes_only_scheduled_execution_and_task_snapshots(self):
        execution_id = self.scheduled_execution()
        response, envelope = self.callback(execution_id, {"status": "completed"})

        self.assertEqual((response.status_code, response.json()), (202, {"status": "applied"}))
        execution = load_workflow_execution_by_id(execution_id, self.database_file)
        tasks = load_workflow_task_executions(execution_id, self.database_file)
        self.assertEqual(execution["status"], "completed")
        self.assertEqual(execution["result_summary"], "Completed by signed integration callback.")
        self.assertEqual(tasks[0]["status"], "completed")
        self.assertEqual(len(load_webhook_deliveries(database_file=self.database_file)), 1)

        headers, body = signed_webhook_headers(
            INBOUND_SECRET, envelope, int(NOW.timestamp()),
        )
        duplicate = self.client.post(
            "/integrations/webhooks/callback", content=body,
            headers={"Content-Type": headers["content_type"], "X-ABAP-Timestamp": headers["timestamp"], "X-ABAP-Event-Id": headers["event_id"], "X-ABAP-Signature": headers["signature"]},
        )
        self.assertEqual((duplicate.status_code, duplicate.json()), (200, {"status": "duplicate"}))

    def test_result_cannot_finish_manual_or_malformed_execution(self):
        manual_id = f"WFE-{uuid4().hex.upper()}"
        self.assertTrue(insert_workflow_execution({
            "execution_id": manual_id, "workflow_id": "WF-RESULT",
            "workflow_name": "Result workflow", "trigger_type": "manual",
            "schedule_occurrence_id": None, "status": "running",
            "started_by_user_id": self.admin["user_id"], "started_at": NOW.isoformat(),
            "finished_at": None, "result_summary": "Manual execution started.",
        }, self.database_file))
        rejected, _ = self.callback(manual_id, {"status": "completed"})
        self.assertEqual(rejected.status_code, 409)
        self.assertEqual(load_workflow_execution_by_id(manual_id, self.database_file)["status"], "running")
        self.assertEqual(load_webhook_deliveries(database_file=self.database_file), [])

        execution_id = self.scheduled_execution()
        malformed, _ = self.callback(execution_id, {"status": "completed", "private_text": "ignore me"})
        self.assertEqual(malformed.status_code, 422)
        self.assertEqual(load_workflow_execution_by_id(execution_id, self.database_file)["status"], "running")


if __name__ == "__main__":
    unittest.main()
