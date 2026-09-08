import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    claim_workflow_schedule_occurrence,
    load_user_account_by_username,
    load_workflow_schedule_occurrences,
)
from models import WorkflowScheduleOccurrence
from schedule_service import (
    claim_due_workflow_schedules,
    evaluate_workflow_schedule,
    find_due_workflow_schedules,
)
from user_service import register_user_account
from workflow_service import (
    create_workflow,
    create_workflow_schedule,
    create_workflow_task,
    set_workflow_schedule_enabled,
    update_workflow,
)


class TestWorkflowScheduleEligibility(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database_file = Path(directory.name) / "eligibility.db"
        register_user_account(
            "admin", "SecurePassword123!", "admin", self.database_file,
        )
        self.admin = load_user_account_by_username("admin", self.database_file)
        self.assertTrue(create_workflow(
            self.admin, "WF-DUE", "Due workflow", "", "draft",
            self.database_file,
        ))
        self.assertTrue(create_workflow_task(
            self.admin, "TASK-DUE", "WF-DUE", 1, "Review request", "",
            "manual", True, self.database_file,
        ))
        self.assertTrue(update_workflow(
            self.admin, "WF-DUE", "Due workflow", "", "active",
            self.database_file,
        ))

    def create_schedule(
        self, schedule_id="SCH-DAILY", schedule_type="daily",
        scheduled_time="09:30", day_of_week="", is_enabled=True,
    ):
        self.assertTrue(create_workflow_schedule(
            self.admin, schedule_id, "WF-DUE", schedule_type,
            scheduled_time, day_of_week, is_enabled, self.database_file,
        ))

    def schedule_record(
        self, schedule_type="daily", scheduled_time="09:30",
        day_of_week=None, is_enabled=True,
    ):
        return {
            "schedule_id": "SCH-UNIT", "workflow_id": "WF-UNIT",
            "schedule_type": schedule_type,
            "scheduled_time": scheduled_time, "day_of_week": day_of_week,
            "is_enabled": is_enabled, "created_by_user_id": 1,
            "created_at": "2026-09-08T00:00:00+00:00",
            "updated_at": "2026-09-08T00:00:00+00:00",
        }

    def test_daily_schedule_uses_business_time_zone_and_five_minute_window(self):
        schedule = self.schedule_record()

        before = evaluate_workflow_schedule(
            schedule, datetime(2026, 9, 8, 1, 29, tzinfo=timezone.utc),
        )
        due = evaluate_workflow_schedule(
            schedule, datetime(2026, 9, 8, 1, 34, 59, tzinfo=timezone.utc),
        )
        expired = evaluate_workflow_schedule(
            schedule, datetime(2026, 9, 8, 1, 35, tzinfo=timezone.utc),
        )

        self.assertFalse(before["is_due"])
        self.assertTrue(due["is_due"])
        self.assertEqual(due["scheduled_for_utc"], "2026-09-08T01:30:00+00:00")
        self.assertFalse(expired["is_due"])
        self.assertEqual(
            expired["next_eligible_at_utc"], "2026-09-09T01:30:00+00:00",
        )

    def test_weekly_schedule_only_matches_configured_local_weekday(self):
        schedule = self.schedule_record(
            "weekly", "10:15", "wednesday",
        )
        tuesday = evaluate_workflow_schedule(
            schedule, datetime(2026, 9, 8, 2, 15, tzinfo=timezone.utc),
        )
        wednesday = evaluate_workflow_schedule(
            schedule, datetime(2026, 9, 9, 2, 17, tzinfo=timezone.utc),
        )

        self.assertFalse(tuesday["is_due"])
        self.assertEqual(
            tuesday["next_eligible_at_utc"], "2026-09-09T02:15:00+00:00",
        )
        self.assertTrue(wednesday["is_due"])

    def test_manual_and_disabled_schedules_are_never_clock_due(self):
        now = datetime(2026, 9, 8, 1, 30, tzinfo=timezone.utc)
        manual = evaluate_workflow_schedule(
            self.schedule_record("manual", None), now,
        )
        disabled = evaluate_workflow_schedule(
            self.schedule_record(is_enabled=False), now,
        )

        self.assertFalse(manual["is_due"])
        self.assertIsNone(manual["next_eligible_at_utc"])
        self.assertFalse(disabled["is_due"])
        self.assertIsNone(disabled["next_eligible_at_utc"])

    def test_evaluator_rejects_naive_time_bad_zone_and_bad_grace_period(self):
        schedule = self.schedule_record()
        with self.assertRaises(ValueError):
            evaluate_workflow_schedule(schedule, datetime(2026, 9, 8, 9, 30))
        with self.assertRaises(ValueError):
            evaluate_workflow_schedule(
                schedule, datetime.now(timezone.utc), "Not/A-Time-Zone",
            )
        with self.assertRaises(ValueError):
            evaluate_workflow_schedule(
                schedule, datetime.now(timezone.utc), grace_minutes=0,
            )

    def test_due_loading_excludes_manual_disabled_and_inactive_schedules(self):
        self.create_schedule()
        self.create_schedule("SCH-MANUAL", "manual", "", "", True)
        self.create_schedule("SCH-OFF", "daily", "09:30", "", False)
        now = datetime(2026, 9, 8, 1, 31, tzinfo=timezone.utc)

        due = find_due_workflow_schedules(now, self.database_file)

        self.assertEqual([item["schedule_id"] for item in due], ["SCH-DAILY"])
        self.assertTrue(update_workflow(
            self.admin, "WF-DUE", "Due workflow", "", "inactive",
            self.database_file,
        ))
        self.assertEqual(find_due_workflow_schedules(now, self.database_file), [])

    def test_due_occurrence_is_claimed_once_across_repeated_checks(self):
        self.create_schedule()
        now = datetime(2026, 9, 8, 1, 32, tzinfo=timezone.utc)

        first = claim_due_workflow_schedules(now, self.database_file)
        second = claim_due_workflow_schedules(now, self.database_file)

        self.assertEqual(len(first), 1)
        self.assertEqual(second, [])
        saved = load_workflow_schedule_occurrences("WF-DUE", self.database_file)
        self.assertEqual(saved, first)
        self.assertEqual(saved[0]["scheduled_for_utc"], "2026-09-08T01:30:00+00:00")

    def test_atomic_claim_rechecks_enabled_and_active_state(self):
        self.create_schedule()
        self.assertTrue(set_workflow_schedule_enabled(
            self.admin, "WF-DUE", "SCH-DAILY", False, self.database_file,
        ))
        occurrence: WorkflowScheduleOccurrence = {
            "occurrence_id": "WFSO-TEST", "schedule_id": "SCH-DAILY",
            "workflow_id": "WF-DUE",
            "scheduled_for_utc": "2026-09-08T01:30:00+00:00",
            "claimed_at": "2026-09-08T01:31:00+00:00",
        }

        self.assertFalse(claim_workflow_schedule_occurrence(
            occurrence, self.database_file,
        ))
        self.assertEqual(
            load_workflow_schedule_occurrences("WF-DUE", self.database_file), [],
        )


if __name__ == "__main__":
    unittest.main()
