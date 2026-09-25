import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from database import load_webhook_deliveries, purge_expired_webhook_replay_events
from webhook_contract import build_webhook_envelope, signed_webhook_headers
from webhook_delivery_service import (
    accept_inbound_webhook,
    queue_outbound_webhook_delivery,
)


SECRET = "inbound-webhook-test-secret"
NOW = datetime(2026, 9, 22, 5, 0, tzinfo=timezone.utc)


def envelope(event_id: str | None = None):
    return build_webhook_envelope(
        event_id or str(uuid4()),
        "WFE-DELIVERY-123",
        "workflow.execution.completed",
        NOW,
        {"private_note": "do-not-store-this-payload", "status": "completed"},
    )


class TestWebhookDeliveryService(unittest.TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.database_file = Path(self.directory.name) / "webhooks.db"

    def accept(self, message):
        headers, body = signed_webhook_headers(
            SECRET, message, int(NOW.timestamp()),
        )
        return accept_inbound_webhook(
            headers, body, SECRET, NOW, 300, 4096, self.database_file,
        )

    def test_verified_inbound_event_is_claimed_once_without_payload_storage(self):
        result = self.accept(envelope())
        deliveries = load_webhook_deliveries(database_file=self.database_file)

        self.assertTrue(result["accepted"])
        self.assertFalse(result["duplicate"])
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0]["direction"], "inbound")
        self.assertEqual(deliveries[0]["status"], "accepted")
        self.assertEqual(deliveries[0]["attempt_count"], 1)
        self.assertNotIn("private_note", str(deliveries[0]))
        self.assertNotIn("do-not-store-this-payload", str(deliveries[0]))
        self.assertNotIn(SECRET, str(deliveries[0]))

    def test_duplicate_verified_callback_is_recorded_once(self):
        message = envelope()
        first = self.accept(message)
        duplicate = self.accept(message)

        self.assertTrue(first["accepted"])
        self.assertFalse(duplicate["accepted"])
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(
            len(load_webhook_deliveries(database_file=self.database_file)), 1,
        )

    def test_concurrent_duplicate_callbacks_create_one_delivery(self):
        message = envelope()
        with ThreadPoolExecutor(max_workers=2) as workers:
            results = list(workers.map(lambda _value: self.accept(message), range(2)))

        self.assertEqual(sum(result["accepted"] for result in results), 1)
        self.assertEqual(
            len(load_webhook_deliveries(database_file=self.database_file)), 1,
        )

    def test_outbound_delivery_starts_pending_and_is_duplicate_safe(self):
        message = envelope()
        created = queue_outbound_webhook_delivery(message, NOW, self.database_file)
        duplicate = queue_outbound_webhook_delivery(message, NOW, self.database_file)
        deliveries = load_webhook_deliveries(database_file=self.database_file)

        self.assertTrue(created)
        self.assertFalse(duplicate)
        self.assertEqual(len(deliveries), 1)
        self.assertEqual(deliveries[0]["direction"], "outbound")
        self.assertEqual(deliveries[0]["status"], "pending")
        self.assertEqual(deliveries[0]["attempt_count"], 0)
        self.assertIsNone(deliveries[0]["response_status"])

    def test_expired_replay_event_is_removed_only_after_its_window(self):
        self.accept(envelope())
        self.assertEqual(
            purge_expired_webhook_replay_events(
                (NOW + timedelta(seconds=299)).isoformat(), self.database_file,
            ),
            0,
        )
        self.assertEqual(
            purge_expired_webhook_replay_events(
                (NOW + timedelta(seconds=301)).isoformat(), self.database_file,
            ),
            1,
        )


if __name__ == "__main__":
    unittest.main()
