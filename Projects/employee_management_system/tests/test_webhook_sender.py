import socket
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from database import load_webhook_deliveries
from integration_config import load_integration_settings
from webhook_contract import build_webhook_envelope, verify_inbound_webhook
from webhook_sender import deliver_outbound_webhook


NOW = datetime(2026, 9, 22, 6, 0, tzinfo=timezone.utc)


def settings(**overrides):
    values = {
        "ABAP_INTEGRATIONS_ENABLED": "true",
        "ABAP_N8N_BASE_URL": "https://automation.example.test",
        "ABAP_N8N_WORKFLOW_PATH": "/webhook/v1/workflow",
        "ABAP_INTEGRATION_ALLOWED_HOSTS": "automation.example.test",
        "ABAP_OUTBOUND_WEBHOOK_SECRET": "outbound-test-secret-1234567890",
        "ABAP_INBOUND_WEBHOOK_SECRET": "inbound-test-secret-1234567890",
        "ABAP_WEBHOOK_MAX_ATTEMPTS": "3",
    }
    values.update(overrides)
    return load_integration_settings(values)


def message():
    return build_webhook_envelope(
        str(uuid4()), "WFE-SENDER-123", "workflow.execution.completed", NOW,
        {"private_note": "never write this body to the database"},
    )


def public_resolver(_host, port, **_kwargs):
    return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", port))]


class FakeResponse:
    def __init__(self, status, body=b""):
        self.status = status
        self._body = body

    def read(self, _amount=-1):
        return self._body


class FakeConnection:
    def __init__(self, response=None, request_error=None):
        self.response = response
        self.request_error = request_error
        self.requests = []
        self.closed = False

    def request(self, method, url, body, headers):
        self.requests.append((method, url, body, headers))
        if self.request_error is not None:
            raise self.request_error

    def getresponse(self):
        return self.response

    def close(self):
        self.closed = True


class TestWebhookSender(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database_file = Path(self.directory.name) / "sender.db"

    def factory(self, connections):
        def create(*_args):
            return connections.pop(0)
        return create

    def test_successful_delivery_is_signed_and_stores_only_safe_result(self):
        connection = FakeConnection(FakeResponse(202, b"accepted"))
        result = deliver_outbound_webhook(
            settings(), message(), NOW, self.database_file, public_resolver,
            self.factory([connection]), lambda _seconds: self.fail("no retry"),
        )
        deliveries = load_webhook_deliveries(database_file=self.database_file)

        self.assertTrue(result["sent"])
        self.assertEqual(result["attempts"], 1)
        self.assertEqual(connection.requests[0][0:2], ("POST", "/webhook/v1/workflow"))
        self.assertIn("X-ABAP-Signature", connection.requests[0][3])
        request_headers = connection.requests[0][3]
        verified = verify_inbound_webhook(
            {
                "content_type": request_headers["Content-Type"],
                "timestamp": request_headers["X-ABAP-Timestamp"],
                "event_id": request_headers["X-ABAP-Event-Id"],
                "signature": request_headers["X-ABAP-Signature"],
            },
            connection.requests[0][2],
            settings()["outbound_secret"] or "",
            NOW,
            300,
            4096,
        )
        self.assertEqual(verified["event_type"], "workflow.execution.completed")
        self.assertTrue(connection.closed)
        self.assertEqual(deliveries[0]["status"], "succeeded")
        self.assertEqual(deliveries[0]["response_status"], 202)
        self.assertNotIn("private_note", str(deliveries[0]))
        self.assertNotIn("accepted", str(deliveries[0]))

    def test_retryable_failure_retries_with_backoff_then_succeeds(self):
        delays = []
        result = deliver_outbound_webhook(
            settings(), message(), NOW, self.database_file, public_resolver,
            self.factory([FakeConnection(FakeResponse(503)), FakeConnection(FakeResponse(201))]),
            delays.append,
        )
        delivery = load_webhook_deliveries(database_file=self.database_file)[0]

        self.assertTrue(result["sent"])
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(delays, [1])
        self.assertEqual(delivery["status"], "succeeded")
        self.assertEqual(delivery["attempt_count"], 2)
        self.assertEqual(delivery["response_status"], 201)

    def test_timeout_retries_only_to_configured_limit_then_fails(self):
        result = deliver_outbound_webhook(
            settings(ABAP_WEBHOOK_MAX_ATTEMPTS="2"), message(), NOW,
            self.database_file, public_resolver,
            self.factory([
                FakeConnection(request_error=TimeoutError()),
                FakeConnection(request_error=TimeoutError()),
            ]),
            lambda _seconds: None,
        )
        delivery = load_webhook_deliveries(database_file=self.database_file)[0]

        self.assertFalse(result["sent"])
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(delivery["status"], "failed")
        self.assertEqual(delivery["attempt_count"], 2)
        self.assertEqual(delivery["failure_code"], "timeout")

    def test_private_dns_redirect_and_large_response_fail_without_retry(self):
        cases = (
            (lambda _host, port, **_kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))], [], "destination_blocked"),
            (public_resolver, [FakeConnection(FakeResponse(302))], "redirect_blocked"),
            (public_resolver, [FakeConnection(FakeResponse(200, b"x" * 33))], "response_too_large"),
        )
        for resolver, connections, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                database_file = (
                    Path(self.directory.name) / f"{expected_code}.db"
                )
                result = deliver_outbound_webhook(
                    settings(ABAP_WEBHOOK_MAX_RESPONSE_BYTES="32"), message(), NOW,
                    database_file, resolver, self.factory(connections),
                    lambda _seconds: self.fail("terminal failure must not retry"),
                )
                delivery = load_webhook_deliveries(database_file=database_file)[0]
                self.assertFalse(result["sent"])
                self.assertEqual(result["attempts"], 1)
                self.assertEqual(delivery["failure_code"], expected_code)

    def test_duplicate_event_is_not_sent_twice(self):
        event = message()
        first_connection = FakeConnection(FakeResponse(200))
        first = deliver_outbound_webhook(
            settings(), event, NOW, self.database_file, public_resolver,
            self.factory([first_connection]), lambda _seconds: None,
        )
        duplicate = deliver_outbound_webhook(
            settings(), event, NOW, self.database_file, public_resolver,
            lambda *_args: self.fail("duplicate must not connect"), lambda _seconds: None,
        )

        self.assertTrue(first["sent"])
        self.assertTrue(duplicate["duplicate"])
        self.assertFalse(duplicate["sent"])
        self.assertEqual(len(load_webhook_deliveries(database_file=self.database_file)), 1)
