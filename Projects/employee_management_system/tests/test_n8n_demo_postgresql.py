import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from uuid import uuid4, uuid5

import psycopg
from psycopg.rows import dict_row

from n8n_demo_provider import CALLBACK_NAMESPACE, N8nDemoEventStore
from postgresql_migrations import apply_postgresql_migrations
from webhook_contract import build_webhook_envelope, canonical_json_bytes


TEST_DATABASE_URL = os.environ.get("ABAP_TEST_DATABASE_URL", "").strip()
NOW = datetime(2026, 10, 14, 2, 0, tzinfo=timezone.utc)


@unittest.skipUnless(
    TEST_DATABASE_URL,
    "ABAP_TEST_DATABASE_URL is required for live PostgreSQL tests.",
)
class TestN8nDemoPostgresql(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        apply_postgresql_migrations(TEST_DATABASE_URL)
        cls.store = N8nDemoEventStore(TEST_DATABASE_URL)

    def setUp(self):
        self.event_ids = []
        self.fixtures = []

    def tearDown(self):
        if not self.event_ids:
            return
        with psycopg.connect(TEST_DATABASE_URL) as connection:
            connection.execute(
                "DELETE FROM n8n_demo_events WHERE event_id = ANY(%s::uuid[])",
                (self.event_ids,),
            )
            for fixture in self.fixtures:
                connection.execute("DELETE FROM workflow_executions WHERE execution_id = %s", (fixture["execution_id"],))
                connection.execute("DELETE FROM workflow_schedule_occurrences WHERE occurrence_id = %s", (fixture["occurrence_id"],))
                connection.execute("DELETE FROM workflow_schedules WHERE schedule_id = %s", (fixture["schedule_id"],))
                connection.execute("DELETE FROM workflows WHERE workflow_id = %s", (fixture["workflow_id"],))
                connection.execute("DELETE FROM users WHERE user_id = %s", (fixture["user_id"],))

    def event(self, suffix=None):
        event_id = str(uuid4())
        self.event_ids.append(event_id)
        suffix = suffix or uuid4().hex[:10].upper()
        envelope = build_webhook_envelope(
            event_id,
            f"WFE-{suffix}",
            "workflow.execution.started",
            NOW,
            {
                "execution_id": f"WFE-{suffix}",
                "workflow_id": f"WF-{suffix}",
                "trigger_type": "schedule",
            },
        )
        return envelope, canonical_json_bytes(envelope)

    def seed_owned_execution(self, envelope):
        marker = uuid4().hex
        fixture = {
            "workflow_id": envelope["data"]["workflow_id"],
            "execution_id": envelope["data"]["execution_id"],
            "schedule_id": f"WFS-{marker}", "occurrence_id": f"WFO-{marker}",
        }
        with psycopg.connect(TEST_DATABASE_URL) as connection:
            fixture["user_id"] = connection.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (%s, 'test-hash', 'admin') RETURNING user_id",
                (f"n8n-phase3-{marker}",),
            ).fetchone()[0]
            connection.execute(
                """INSERT INTO workflows
                   (workflow_id, name, description, status, created_by_user_id, created_at, updated_at)
                   VALUES (%s, 'Phase 3 test', '', 'active', %s, %s, %s)""",
                (fixture["workflow_id"], fixture["user_id"], NOW, NOW),
            )
            connection.execute(
                """INSERT INTO workflow_schedules
                   (schedule_id, workflow_id, schedule_type, scheduled_time, day_of_week,
                    is_enabled, created_by_user_id, created_at, updated_at)
                   VALUES (%s, %s, 'daily', '02:00', NULL, TRUE, %s, %s, %s)""",
                (fixture["schedule_id"], fixture["workflow_id"], fixture["user_id"], NOW, NOW),
            )
            connection.execute(
                """INSERT INTO workflow_schedule_occurrences
                   (occurrence_id, schedule_id, workflow_id, scheduled_for_utc, claimed_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (fixture["occurrence_id"], fixture["schedule_id"], fixture["workflow_id"], NOW, NOW),
            )
            connection.execute(
                """INSERT INTO workflow_executions
                   (execution_id, workflow_id, workflow_name, trigger_type,
                    schedule_occurrence_id, status, started_at)
                   VALUES (%s, %s, 'Phase 3 test', 'schedule', %s, 'running', %s)""",
                (fixture["execution_id"], fixture["workflow_id"], fixture["occurrence_id"], NOW),
            )
        self.fixtures.append(fixture)

    def test_concurrent_duplicate_acceptance_is_atomic(self):
        envelope, body = self.event()

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(
                lambda _index: self.store.accept(envelope, body, NOW), range(8),
            ))

        self.assertEqual(results.count("accepted"), 1)
        self.assertEqual(results.count("duplicate"), 7)
        with psycopg.connect(TEST_DATABASE_URL) as connection:
            count = connection.execute(
                "SELECT COUNT(*) FROM n8n_demo_events WHERE event_id = %s",
                (envelope["event_id"],),
            ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_two_workers_claim_distinct_events(self):
        first, first_body = self.event("CLAIM-A")
        second, second_body = self.event("CLAIM-B")
        self.store.accept(first, first_body, NOW)
        self.store.accept(second, second_body, NOW)

        with ThreadPoolExecutor(max_workers=2) as executor:
            claims = list(executor.map(
                lambda _index: self.store.claim(NOW, 30, 3), range(2),
            ))

        self.assertEqual(len({claim["event_id"] for claim in claims}), 2)

    def test_n8n_restart_after_durable_acceptance_preserves_the_event(self):
        envelope, body = self.event("N8N-RESTART")
        accepting_process = N8nDemoEventStore(TEST_DATABASE_URL)
        self.assertEqual(accepting_process.accept(envelope, body, NOW), "accepted")

        restarted_process = N8nDemoEventStore(TEST_DATABASE_URL)
        claim = restarted_process.claim(NOW, 30, 3)
        self.assertEqual(claim["event_id"], envelope["event_id"])

    def test_expired_lease_is_recovered_with_stable_callback_id(self):
        envelope, body = self.event("RECOVERY")
        self.store.accept(envelope, body, NOW)
        first = self.store.claim(NOW, 1, 3)

        restarted_store = N8nDemoEventStore(TEST_DATABASE_URL)
        recovered = restarted_store.claim(NOW + timedelta(seconds=2), 30, 3)

        self.assertEqual(recovered["event_id"], first["event_id"])
        with psycopg.connect(TEST_DATABASE_URL) as connection:
            callback_event_id, attempt_count = connection.execute(
                "SELECT callback_event_id::text, attempt_count FROM n8n_demo_events WHERE event_id = %s",
                (envelope["event_id"],),
            ).fetchone()
        self.assertEqual(callback_event_id, str(uuid5(CALLBACK_NAMESPACE, envelope["event_id"])))
        self.assertEqual(attempt_count, 2)

    def test_outcome_is_bound_to_owned_running_execution_and_is_single_use(self):
        envelope, body = self.event("COMPLETE")
        self.seed_owned_execution(envelope)
        self.store.accept(envelope, body, NOW)
        claim = self.store.claim(NOW, 30, 3)

        prepared = self.store.prepare_outcome(claim["event_id"], "completed", NOW)
        self.assertEqual(prepared["callback_event_id"], str(uuid5(CALLBACK_NAMESPACE, claim["event_id"])))
        self.assertIsNone(self.store.prepare_outcome(claim["event_id"], "completed", NOW))
        self.assertTrue(self.store.complete_outcome(claim["event_id"], "completed", NOW))
        self.assertFalse(self.store.complete_outcome(claim["event_id"], "completed", NOW))

    def test_concurrent_duplicate_outcomes_allow_one_callback_owner(self):
        envelope, body = self.event("OUTCOME-RACE")
        self.seed_owned_execution(envelope)
        self.store.accept(envelope, body, NOW)
        claim = self.store.claim(NOW, 30, 3)
        with ThreadPoolExecutor(max_workers=8) as executor:
            outcomes = list(executor.map(
                lambda _index: self.store.prepare_outcome(claim["event_id"], "completed", NOW),
                range(8),
            ))
        self.assertEqual(sum(outcome is not None for outcome in outcomes), 1)

    def test_restart_after_abap_applies_callback_reuses_stable_identity(self):
        envelope, body = self.event("POST-CALLBACK-CRASH")
        self.seed_owned_execution(envelope)
        self.store.accept(envelope, body, NOW)
        first_claim = self.store.claim(NOW, 1, 3)
        first = self.store.prepare_outcome(first_claim["event_id"], "completed", NOW)
        with psycopg.connect(TEST_DATABASE_URL) as connection:
            connection.execute(
                "UPDATE workflow_executions SET status = 'completed', finished_at = %s WHERE execution_id = %s",
                (NOW, envelope["data"]["execution_id"]),
            )
        restarted = N8nDemoEventStore(TEST_DATABASE_URL)
        second_claim = restarted.claim(NOW + timedelta(seconds=2), 30, 3)
        self.assertEqual(restarted.synthetic_action(second_claim["event_id"], NOW + timedelta(seconds=2)), "completed")
        second = restarted.prepare_outcome(second_claim["event_id"], "completed", NOW + timedelta(seconds=2))
        self.assertEqual(second["callback_event_id"], first["callback_event_id"])

    def test_outcome_rejects_unclaimed_expired_and_non_running_ownership(self):
        unclaimed, body = self.event("UNCLAIMED")
        self.seed_owned_execution(unclaimed)
        self.store.accept(unclaimed, body, NOW)
        self.assertIsNone(self.store.prepare_outcome(unclaimed["event_id"], "completed", NOW))
        with psycopg.connect(TEST_DATABASE_URL) as connection:
            connection.execute("DELETE FROM n8n_demo_events WHERE event_id = %s", (unclaimed["event_id"],))

        expired, body = self.event("EXPIRED")
        self.seed_owned_execution(expired)
        self.store.accept(expired, body, NOW)
        self.store.claim(NOW, 1, 3)
        self.assertIsNone(self.store.prepare_outcome(expired["event_id"], "completed", NOW + timedelta(seconds=2)))
        with psycopg.connect(TEST_DATABASE_URL) as connection:
            connection.execute("DELETE FROM n8n_demo_events WHERE event_id = %s", (expired["event_id"],))

        mismatched, body = self.event("MISMATCHED")
        self.seed_owned_execution(mismatched)
        self.store.accept(mismatched, body, NOW)
        self.store.claim(NOW + timedelta(seconds=2), 30, 3)
        with psycopg.connect(TEST_DATABASE_URL) as connection:
            connection.execute(
                "UPDATE workflow_executions SET status = 'completed', finished_at = %s WHERE execution_id = %s",
                (NOW, mismatched["data"]["execution_id"]),
            )
        self.assertIsNone(self.store.prepare_outcome(mismatched["event_id"], "completed", NOW + timedelta(seconds=2)))

    def test_repeated_callback_failure_becomes_bounded_dead_event(self):
        envelope, body = self.event("CALLBACK-FAILURE")
        self.seed_owned_execution(envelope)
        self.store.accept(envelope, body, NOW)
        callback_ids = set()
        for attempt in range(3):
            current_time = NOW + timedelta(seconds=attempt * 2)
            claim = self.store.claim(
                current_time, 1, 3,
            )
            self.assertEqual(claim["event_id"], envelope["event_id"])
            outcome = self.store.prepare_outcome(
                claim["event_id"], "completed", current_time,
            )
            callback_ids.add(outcome["callback_event_id"])
            for _callback_attempt in range(3):
                self.store.record_callback_attempt(claim["event_id"], current_time)
            self.store.record_callback_failure(claim["event_id"], current_time)

        self.assertIsNone(self.store.claim(NOW + timedelta(seconds=6), 1, 3))
        with psycopg.connect(TEST_DATABASE_URL, row_factory=dict_row) as connection:
            row = connection.execute(
                """
                SELECT status, attempt_count, callback_attempt_count,
                       failure_code, callback_event_id::text
                  FROM n8n_demo_events
                 WHERE event_id = %s
                """,
                (envelope["event_id"],),
            ).fetchone()
        self.assertEqual(
            (row["status"], row["attempt_count"], row["callback_attempt_count"],
             row["failure_code"]),
            ("dead", 3, 9, "retry_exhausted"),
        )
        self.assertEqual(row["callback_event_id"], str(uuid5(CALLBACK_NAMESPACE, envelope["event_id"])))
        self.assertEqual(callback_ids, {row["callback_event_id"]})


if __name__ == "__main__":
    unittest.main()
