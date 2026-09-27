import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from unittest.mock import patch

from fastapi.testclient import TestClient
from tests.web_auth import sign_in, sign_out

from database import load_webhook_deliveries
from abuse_protection import WebhookCircuitBreaker
from integration_config import load_integration_settings
from user_service import register_user_account
from web_app import create_web_application
from webhook_contract import build_webhook_envelope, signed_webhook_headers


NOW = datetime(2026, 9, 22, 8, 0, tzinfo=timezone.utc)
INBOUND_SECRET = "inbound-webhook-test-secret-1234567890"


def enabled_settings(**overrides):
    values = {
        "ABAP_INTEGRATIONS_ENABLED": "true",
        "ABAP_N8N_BASE_URL": "https://automation.example.test",
        "ABAP_N8N_WORKFLOW_PATH": "/webhook/v1/workflow",
        "ABAP_INTEGRATION_ALLOWED_HOSTS": "automation.example.test",
        "ABAP_OUTBOUND_WEBHOOK_SECRET": "outbound-webhook-test-secret-1234567890",
        "ABAP_INBOUND_WEBHOOK_SECRET": INBOUND_SECRET,
        "ABAP_WEBHOOK_MAX_REQUEST_BYTES": "512",
    }
    values.update(overrides)
    return load_integration_settings(values)


class TestWebhookWebBoundary(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database_file = Path(directory.name) / "webhook-web.db"
        register_user_account("admin", "SecurePassword123!", "admin", self.database_file)
        register_user_account("viewer", "SecurePassword123!", "viewer", self.database_file)
        self.settings = enabled_settings()
        self.application = create_web_application(
            database_file=self.database_file,
            session_secret="webhook-web-test-session-secret",
            integration_settings_loader=lambda: self.settings,
            webhook_clock=lambda: NOW,
        )
        self.client = TestClient(self.application)
        self.addCleanup(self.client.close)

    def message(self):
        return build_webhook_envelope(
            str(uuid4()),
            "WFE-CALLBACK-123",
            "workflow.execution.completed",
            NOW,
            {"private_note": "never display this webhook payload"},
        )

    def signed_callback(self, message=None):
        headers, body = signed_webhook_headers(
            INBOUND_SECRET,
            message or self.message(),
            int(NOW.timestamp()),
        )
        return body, {
            "Content-Type": headers["content_type"],
            "X-ABAP-Timestamp": headers["timestamp"],
            "X-ABAP-Event-Id": headers["event_id"],
            "X-ABAP-Signature": headers["signature"],
        }

    def submit_callback(self, message=None):
        body, headers = self.signed_callback(message)
        return self.client.post(
            "/integrations/webhooks/callback",
            content=body,
            headers=headers,
        )

    def sign_in(self, username):
        return sign_in(self.client, username, "SecurePassword123!")

    def test_signed_callback_is_accepted_once_without_a_session_or_payload_storage(self):
        message = self.message()
        first = self.submit_callback(message)
        duplicate = self.submit_callback(message)
        deliveries = load_webhook_deliveries(database_file=self.database_file)

        self.assertEqual(first.status_code, 202)
        self.assertEqual(first.json(), {"status": "accepted"})
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(duplicate.json(), {"status": "duplicate"})
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0]["status"], "accepted")
        self.assertNotIn("private_note", str(deliveries[0]))
        self.assertNotIn("never display this webhook payload", str(deliveries[0]))
        self.assertNotIn(INBOUND_SECRET, str(deliveries[0]))

    def test_callback_rejects_invalid_signatures_and_oversized_bodies(self):
        invalid = self.client.post(
            "/integrations/webhooks/callback",
            content=b'{"not":"signed"}',
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(invalid.status_code, 401)
        self.assertEqual(
            load_webhook_deliveries(database_file=self.database_file),
            [],
        )

        oversized = self.client.post(
            "/integrations/webhooks/callback",
            content=b"x" * 513,
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(oversized.status_code, 413)
        self.assertEqual(
            load_webhook_deliveries(database_file=self.database_file),
            [],
        )

    def test_callback_fails_closed_when_integrations_are_disabled(self):
        self.settings = load_integration_settings({})
        response = self.submit_callback()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            load_webhook_deliveries(database_file=self.database_file),
            [],
        )

    def test_callback_circuit_breaker_precedes_body_and_ignores_forwarded_headers(self):
        limiter = WebhookCircuitBreaker(
            source_limit=1,
            process_limit=10,
            window_seconds=60,
            max_sources=4,
            clock=lambda: 1000.0,
        )
        application = create_web_application(
            database_file=self.database_file,
            session_secret="webhook-limiter-test-session-secret",
            integration_settings_loader=lambda: self.settings,
            webhook_clock=lambda: NOW,
            webhook_circuit_breaker=limiter,
        )
        client = TestClient(application)
        self.addCleanup(client.close)

        first = client.post(
            "/integrations/webhooks/callback",
            content=b"{}",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(first.status_code, 401)

        with (
            patch("web_app.read_bounded_request_body") as read_body,
            patch("web_app.verify_inbound_webhook") as verify,
            patch("web_app.accept_inbound_webhook") as accept,
        ):
            rejected = client.post(
                "/integrations/webhooks/callback",
                content=b"unread body",
                headers={
                    "Content-Type": "application/json",
                    "X-Forwarded-For": "198.51.100.22",
                    "Forwarded": "for=203.0.113.9",
                },
            )

        self.assertEqual(rejected.status_code, 429)
        self.assertEqual(rejected.json(), {"detail": "Too many webhook requests."})
        self.assertEqual(rejected.headers["retry-after"], "60")
        read_body.assert_not_called()
        verify.assert_not_called()
        accept.assert_not_called()
        self.assertEqual(
            load_webhook_deliveries(database_file=self.database_file),
            [],
        )

    def test_delivery_history_is_admin_only_and_never_renders_payload_data(self):
        message = self.message()
        self.assertEqual(self.submit_callback(message).status_code, 202)

        self.sign_in("admin")
        response = self.client.get("/integrations/webhooks")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Webhook deliveries", response.text)
        self.assertIn(message["event_type"], response.text)
        self.assertIn(message["correlation_id"], response.text)
        self.assertNotIn("private_note", response.text)
        self.assertNotIn("never display this webhook payload", response.text)
        self.assertNotIn(INBOUND_SECRET, response.text)

        sign_out(self.client)
        self.sign_in("viewer")
        denied = self.client.get("/integrations/webhooks")
        self.assertEqual(denied.status_code, 403)

        guest = TestClient(self.application)
        self.addCleanup(guest.close)
        unauthenticated = guest.get(
            "/integrations/webhooks",
            follow_redirects=False,
        )
        self.assertEqual(unauthenticated.status_code, 303)


if __name__ == "__main__":
    unittest.main()
