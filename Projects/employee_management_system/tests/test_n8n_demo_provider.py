import base64
import http.client
import json
import threading
import unittest
from unittest.mock import mock_open, patch
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from uuid import uuid4, uuid5

import psycopg

from n8n_demo_provider import CALLBACK_NAMESPACE, N8nDemoServer, _read_secret_file
from webhook_contract import (
    build_webhook_envelope, signed_webhook_headers, verify_inbound_webhook,
)


NOW = datetime(2026, 10, 14, 2, 0, tzinfo=timezone.utc)
OUTBOUND_SECRET = "phase-three-outbound-test-secret-123456"
INBOUND_SECRET = "phase-three-inbound-test-secret-1234567"
INTERNAL_TOKEN = "phase-three-provider-token-123456789012"
CALLBACK_URL = "http://web:8000/integrations/webhooks/callback"


class MemoryStore:
    def __init__(self):
        self.events = {}
        self.claimed = None
        self.action_status = None
        self.outcome = None
        self.completed = None
        self.callback_attempts = 0
        self.callback_failure = False

    def accept(self, envelope, raw_body, _accepted_at):
        existing = self.events.get(envelope["event_id"])
        if existing is not None:
            if existing != raw_body:
                raise ValueError("collision")
            return "duplicate"
        self.events[envelope["event_id"]] = raw_body
        return "accepted"

    def claim(self, _claimed_at, _lease_seconds, _max_attempts):
        return self.claimed

    def synthetic_action(self, _event_id, _current_time):
        return self.action_status

    def prepare_outcome(self, _event_id, result_status, _current_time):
        if self.outcome is None or self.outcome["result_status"] != result_status:
            return None
        outcome = self.outcome
        self.outcome = None
        return outcome

    def record_callback_attempt(self, _event_id, _recorded_at):
        self.callback_attempts += 1

    def record_callback_failure(self, _event_id, _recorded_at):
        self.callback_failure = True

    def complete_outcome(self, event_id, result_status, _completed_at):
        self.completed = (event_id, result_status)
        return True


class TestN8nDemoProvider(unittest.TestCase):
    def setUp(self):
        self.store = MemoryStore()
        self.callbacks = []
        self.callback_statuses = [HTTPStatus.OK]

        def send_callback(url, headers, body, timeout):
            self.callbacks.append((url, headers, body, timeout))
            status = self.callback_statuses.pop(0)
            return status

        self.server = N8nDemoServer(
            ("127.0.0.1", 0), self.store, INTERNAL_TOKEN, OUTBOUND_SECRET,
            INBOUND_SECRET, CALLBACK_URL, clock=lambda: NOW,
            callback_sender=send_callback, sleeper=lambda _seconds: None,
        )
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def request(self, path: str, value, token: str = INTERNAL_TOKEN):
        body = value if isinstance(value, bytes) else json.dumps(value).encode()
        connection = http.client.HTTPConnection(*self.server.server_address)
        connection.request("POST", path, body, {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
        })
        response = connection.getresponse()
        result = response.status, response.read()
        connection.close()
        return result

    def signed_acceptance(
        self, timestamp=None, event_id=None, body_event_id=None,
        signature_secret=OUTBOUND_SECRET, extra_data=None,
    ):
        event_id = event_id or str(uuid4())
        body_event_id = body_event_id or event_id
        data = {"execution_id": "WFE-N8N-DEMO-1", "workflow_id": "WF-N8N-DEMO",
                "trigger_type": "schedule"}
        if extra_data:
            data.update(extra_data)
        envelope = build_webhook_envelope(
            body_event_id, data["execution_id"], "workflow.execution.started", NOW, data,
        )
        headers, body = signed_webhook_headers(
            signature_secret, envelope, int((timestamp or NOW).timestamp()),
        )
        return {"raw_body_base64": base64.b64encode(body).decode("ascii"),
                "content_type": headers["content_type"], "timestamp": headers["timestamp"],
                "event_id": event_id, "signature": headers["signature"]}

    def prepare_claimed_outcome(self, result_status="completed"):
        event_id = str(uuid4())
        callback_id = str(uuid5(CALLBACK_NAMESPACE, event_id))
        self.store.outcome = {
            "event_id": event_id, "correlation_id": "WFE-N8N-DEMO-1",
            "workflow_id": "WF-N8N-DEMO", "callback_event_id": callback_id,
            "callback_occurred_at": NOW, "result_status": result_status,
        }
        return event_id, callback_id

    def test_accepts_once_then_reports_duplicate_before_side_effects(self):
        request = self.signed_acceptance()
        first = self.request("/accept", request)
        second = self.request("/accept", request)
        self.assertEqual(first[0], HTTPStatus.ACCEPTED)
        self.assertEqual(json.loads(first[1])["status"], "accepted")
        self.assertEqual(second[0], HTTPStatus.OK)
        self.assertEqual(json.loads(second[1])["status"], "duplicate")
        self.assertEqual(len(self.store.events), 1)

    def test_postgresql_outage_before_acceptance_returns_no_acknowledgment(self):
        self.store.accept = lambda *_args: (_ for _ in ()).throw(
            psycopg.OperationalError("synthetic outage")
        )
        status, body = self.request("/accept", self.signed_acceptance())
        self.assertEqual(status, HTTPStatus.SERVICE_UNAVAILABLE)
        self.assertEqual(json.loads(body), {"status": "unavailable"})

    def test_rejects_invalid_signature_and_wrong_provider_token(self):
        invalid = self.signed_acceptance(signature_secret="different-secret")
        self.assertEqual(self.request("/accept", invalid)[0], HTTPStatus.BAD_REQUEST)
        self.assertEqual(self.request("/accept", self.signed_acceptance(), "wrong-token")[0], HTTPStatus.UNAUTHORIZED)
        self.assertEqual(self.store.events, {})

    def test_rejects_expired_future_mismatched_and_malformed_ingress(self):
        expired = self.signed_acceptance(timestamp=NOW - timedelta(seconds=301))
        future = self.signed_acceptance(timestamp=NOW + timedelta(seconds=61))
        mismatch = self.signed_acceptance(event_id=str(uuid4()), body_event_id=str(uuid4()))
        malformed = self.signed_acceptance(extra_data={"customer": "must-not-pass"})
        for request in (expired, future, mismatch, malformed):
            self.assertEqual(self.request("/accept", request)[0], HTTPStatus.BAD_REQUEST)
        status, body = self.request("/accept", b'{"private_payload":"do not echo"}')
        self.assertEqual(status, HTTPStatus.BAD_REQUEST)
        self.assertNotIn(b"private_payload", body)

    def test_claim_exposes_only_event_identifier(self):
        event_id = str(uuid4())
        self.store.claimed = {"event_id": event_id, "callback_event_id": str(uuid4())}
        status, body = self.request("/claim", {})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(json.loads(body), {"claimed": True, "event_id": event_id})

    def test_action_rejects_unknown_or_unleased_event(self):
        event_id = str(uuid4())
        self.assertEqual(self.request("/demo-action", {"event_id": event_id})[0], HTTPStatus.BAD_REQUEST)
        self.store.action_status = "completed"
        self.assertEqual(json.loads(self.request("/demo-action", {"event_id": event_id})[1]), {"status": "completed"})
        self.assertEqual(self.request("/demo-action", {"event_id": event_id, "workflow_id": "forged"})[0], HTTPStatus.BAD_REQUEST)

    def test_service_constructs_and_signs_callback_without_exposing_it(self):
        event_id, callback_id = self.prepare_claimed_outcome()
        status, response_body = self.request("/outcome", {"event_id": event_id, "result_status": "completed"})
        self.assertEqual(status, HTTPStatus.OK)
        self.assertEqual(json.loads(response_body), {"status": "completed"})
        self.assertNotIn(b"signature", response_body)
        self.assertNotIn(callback_id.encode(), response_body)
        url, headers, body, timeout = self.callbacks[0]
        verified = verify_inbound_webhook(headers, body, INBOUND_SECRET, NOW, 300, 262_144)
        self.assertEqual(url, CALLBACK_URL)
        self.assertEqual(timeout, 3)
        self.assertEqual(verified["event_id"], callback_id)
        self.assertEqual(verified["data"], {"status": "completed"})
        self.assertEqual(self.store.completed, (event_id, "completed"))

    def test_duplicate_or_mismatched_outcome_is_rejected(self):
        event_id, _callback_id = self.prepare_claimed_outcome()
        self.assertEqual(self.request("/outcome", {"event_id": event_id, "result_status": "failed"})[0], HTTPStatus.BAD_REQUEST)
        self.assertEqual(self.request("/outcome", {"event_id": event_id, "result_status": "completed"})[0], HTTPStatus.OK)
        self.assertEqual(self.request("/outcome", {"event_id": event_id, "result_status": "completed"})[0], HTTPStatus.BAD_REQUEST)
        self.assertEqual(len(self.callbacks), 1)

    def test_callback_retries_are_bounded_and_keep_stable_identity(self):
        event_id, callback_id = self.prepare_claimed_outcome("failed")
        self.callback_statuses = [500, 502, 503]
        status, body = self.request("/outcome", {"event_id": event_id, "result_status": "failed"})
        self.assertEqual(status, HTTPStatus.SERVICE_UNAVAILABLE)
        self.assertEqual(json.loads(body), {"status": "unavailable"})
        self.assertEqual(self.store.callback_attempts, 3)
        self.assertTrue(self.store.callback_failure)
        self.assertEqual({json.loads(item[2])["event_id"] for item in self.callbacks}, {callback_id})

    def test_lost_callback_response_recovers_with_same_callback_identity(self):
        event_id, callback_id = self.prepare_claimed_outcome()
        original_outcome = dict(self.store.outcome)

        def lose_response(url, headers, body, timeout):
            self.callbacks.append((url, headers, body, timeout))
            raise TimeoutError("synthetic response loss")

        self.server.callback_sender = lose_response
        self.assertEqual(
            self.request("/outcome", {"event_id": event_id, "result_status": "completed"})[0],
            HTTPStatus.SERVICE_UNAVAILABLE,
        )
        self.store.outcome = original_outcome
        self.server.callback_sender = lambda url, headers, body, timeout: (
            self.callbacks.append((url, headers, body, timeout)) or HTTPStatus.OK
        )
        self.assertEqual(
            self.request("/outcome", {"event_id": event_id, "result_status": "completed"})[0],
            HTTPStatus.OK,
        )
        self.assertEqual(
            {json.loads(callback[2])["event_id"] for callback in self.callbacks},
            {callback_id},
        )
        self.assertEqual(self.store.completed, (event_id, "completed"))


class TestProviderTokenFile(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data=b"a" * 32 + b"\n")
    @patch("os.lstat")
    def test_reads_regular_secret_file(self, lstat, _open):
        lstat.return_value.st_mode = 0o100400
        lstat.return_value.st_size = 33
        self.assertEqual(_read_secret_file("C:\\run\\secrets\\token", 32), "a" * 32)

    def test_rejects_relative_secret_path(self):
        with self.assertRaisesRegex(RuntimeError, "absolute"):
            _read_secret_file("token", 32)


if __name__ == "__main__":
    unittest.main()
