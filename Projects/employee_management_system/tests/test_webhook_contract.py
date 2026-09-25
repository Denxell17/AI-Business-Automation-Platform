import unittest
from datetime import datetime, timedelta, timezone

from webhook_contract import (
    WEBHOOK_SCHEMA_VERSION,
    build_webhook_envelope,
    canonical_json_bytes,
    sign_webhook_body,
    signed_webhook_headers,
    verify_inbound_webhook,
)


SECRET = "test-inbound-signing-secret"
EVENT_ID = "0f8fad5b-d9cb-469f-a165-70867728950e"
NOW = datetime(2026, 9, 22, 4, 0, tzinfo=timezone.utc)


def valid_envelope():
    return build_webhook_envelope(
        EVENT_ID,
        "WFE-EXAMPLE-123",
        "workflow.execution.completed",
        NOW,
        {"status": "completed", "count": 1},
    )


class TestWebhookContract(unittest.TestCase):
    def test_canonical_json_is_stable_and_valid_message_round_trips(self):
        envelope = valid_envelope()
        headers, body = signed_webhook_headers(SECRET, envelope, int(NOW.timestamp()))

        verified = verify_inbound_webhook(headers, body, SECRET, NOW, 300, 1024)

        self.assertEqual(verified, envelope)
        self.assertEqual(
            canonical_json_bytes({"b": 1, "a": 2}),
            b'{"a":2,"b":1}',
        )
        self.assertEqual(verified["schema_version"], WEBHOOK_SCHEMA_VERSION)

    def test_modified_body_or_header_or_secret_fails_signature_check(self):
        headers, body = signed_webhook_headers(SECRET, valid_envelope(), int(NOW.timestamp()))
        cases = (
            (headers, body.replace(b"completed", b"failed"), SECRET),
            ({**headers, "event_id": "d9428888-122b-11e1-b85c-61cd3cbb3210"}, body, SECRET),
            (headers, body, "different-test-secret"),
        )
        for supplied_headers, supplied_body, supplied_secret in cases:
            with self.subTest():
                with self.assertRaisesRegex(ValueError, "signature"):
                    verify_inbound_webhook(
                        supplied_headers, supplied_body, supplied_secret, NOW, 300, 1024,
                    )

    def test_stale_and_future_timestamps_are_rejected(self):
        envelope = valid_envelope()
        for timestamp in (int((NOW - timedelta(seconds=301)).timestamp()), int((NOW + timedelta(seconds=61)).timestamp())):
            with self.subTest(timestamp=timestamp):
                headers, body = signed_webhook_headers(SECRET, envelope, timestamp)
                with self.assertRaisesRegex(ValueError, "timestamp"):
                    verify_inbound_webhook(headers, body, SECRET, NOW, 300, 1024)

    def test_oversized_non_json_and_wrong_content_type_are_rejected(self):
        headers, body = signed_webhook_headers(SECRET, valid_envelope(), int(NOW.timestamp()))
        with self.assertRaisesRegex(ValueError, "size"):
            verify_inbound_webhook(headers, body, SECRET, NOW, 300, len(body) - 1)
        with self.assertRaisesRegex(ValueError, "content type"):
            verify_inbound_webhook({**headers, "content_type": "text/plain"}, body, SECRET, NOW, 300, 1024)
        signed_invalid_json = b"not json"
        invalid_headers = {
            **headers,
            "signature": sign_webhook_body(
                SECRET, int(NOW.timestamp()), EVENT_ID, signed_invalid_json,
            ),
        }
        with self.assertRaisesRegex(ValueError, "valid JSON"):
            verify_inbound_webhook(invalid_headers, signed_invalid_json, SECRET, NOW, 300, 1024)

    def test_schema_rejects_unknown_fields_noncanonical_ids_and_unsafe_data(self):
        envelope = valid_envelope()
        invalid_cases = (
            {**envelope, "unexpected": True},
            {**envelope, "event_id": EVENT_ID.upper()},
            {**envelope, "occurred_at": "2026-09-22T04:00:00"},
            {**envelope, "data": ["not", "an", "object"]},
        )
        for malformed in invalid_cases:
            with self.subTest():
                body = canonical_json_bytes(malformed)
                headers, _ = signed_webhook_headers(SECRET, envelope, int(NOW.timestamp()))
                headers["signature"] = sign_webhook_body(
                    SECRET, int(NOW.timestamp()), EVENT_ID, body,
                )
                with self.assertRaises(ValueError):
                    verify_inbound_webhook(headers, body, SECRET, NOW, 300, 1024)
        with self.assertRaises(ValueError):
            build_webhook_envelope(
                EVENT_ID, "WFE-EXAMPLE-123", "workflow.execution.completed", NOW,
                {"nan": float("nan")},
            )

    def test_message_construction_rejects_naive_time_and_bad_identifiers(self):
        with self.assertRaisesRegex(ValueError, "time zone"):
            build_webhook_envelope(EVENT_ID, "WFE-EXAMPLE-123", "workflow.execution.completed", datetime(2026, 9, 22), {})
        with self.assertRaises(ValueError):
            build_webhook_envelope("not-a-uuid", "WFE-EXAMPLE-123", "workflow.execution.completed", NOW, {})
        with self.assertRaises(ValueError):
            build_webhook_envelope(EVENT_ID, "bad value", "workflow.execution.completed", NOW, {})
        with self.assertRaises(ValueError):
            build_webhook_envelope(EVENT_ID, "WFE-EXAMPLE-123", "Workflow Completed", NOW, {})


if __name__ == "__main__":
    unittest.main()
