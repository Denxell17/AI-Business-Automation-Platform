import re
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from database import (
    load_user_account_by_username,
    load_workflow_schedule_by_id,
    load_workflow_schedules,
)
from user_service import register_user_account
from web_app import create_web_application
from workflow_service import (
    create_workflow,
    create_workflow_schedule,
    create_workflow_task,
    set_workflow_schedule_enabled,
    update_workflow,
)


class TestWorkflowSchedules(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database_file = Path(directory.name) / "schedules.db"
        for role in ("admin", "viewer"):
            register_user_account(role, "SecurePassword123!", role, self.database_file)
        self.admin = load_user_account_by_username("admin", self.database_file)
        self.viewer = load_user_account_by_username("viewer", self.database_file)
        self.assertTrue(create_workflow(
            self.admin, "WF-SCHEDULE", "Scheduled workflow", "", "draft",
            self.database_file,
        ))
        self.assertTrue(create_workflow_task(
            self.admin, "TASK-1", "WF-SCHEDULE", 1, "Review work", "",
            "manual", True, self.database_file,
        ))
        self.assertTrue(update_workflow(
            self.admin, "WF-SCHEDULE", "Scheduled workflow", "", "active",
            self.database_file,
        ))
        self.application = create_web_application(
            database_file=self.database_file,
            session_secret="workflow-schedule-tests",
        )
        self.client = TestClient(self.application)
        self.addCleanup(self.client.close)
        logger = patch("web_app.log_activity")
        self.log = logger.start()
        self.addCleanup(logger.stop)

    def create_schedule(
        self, schedule_id="SCH-1", schedule_type="daily",
        scheduled_time="09:30", day_of_week="", is_enabled=True,
        current_user=None, workflow_id="WF-SCHEDULE",
    ):
        return create_workflow_schedule(
            current_user or self.admin, schedule_id, workflow_id, schedule_type,
            scheduled_time, day_of_week, is_enabled, self.database_file,
        )

    def sign_in(self, username="admin"):
        self.client.post(
            "/login",
            data={"username": username, "password": "SecurePassword123!"},
        )
        self.log.reset_mock()

    def csrf_token(self):
        response = self.client.get("/workflows/WF-SCHEDULE")
        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', response.text)
        self.assertIsNotNone(match)
        return match.group(1)

    def test_repository_round_trip_orders_and_scopes_schedules(self):
        self.assertTrue(self.create_schedule(
            " sch-daily ", " DAILY ", "09:30", "monday", True,
        ))
        self.assertTrue(self.create_schedule(
            "SCH-WEEKLY", "weekly", "17:05", " FRIDAY ", False,
        ))
        self.assertTrue(self.create_schedule(
            "SCH-MANUAL", "manual", "11:00", "tuesday", True,
        ))
        schedules = load_workflow_schedules("WF-SCHEDULE", self.database_file)
        self.assertEqual([item["schedule_id"] for item in schedules], [
            "SCH-DAILY", "SCH-WEEKLY", "SCH-MANUAL",
        ])
        daily, weekly, manual = schedules
        self.assertEqual((daily["scheduled_time"], daily["day_of_week"]), ("09:30", None))
        self.assertEqual((weekly["scheduled_time"], weekly["day_of_week"]), ("17:05", "friday"))
        self.assertEqual((manual["scheduled_time"], manual["day_of_week"]), (None, None))
        self.assertIs(manual["is_enabled"], True)
        self.assertEqual(load_workflow_schedules("MISSING", self.database_file), [])
        self.assertEqual(load_workflow_schedule_by_id("SCH-WEEKLY", self.database_file), weekly)

    def test_schedule_validation_rejects_invalid_rules_without_writes(self):
        cases = (
            {"schedule_id": " "},
            {"schedule_type": "monthly"},
            {"schedule_type": "daily", "scheduled_time": "9:30"},
            {"schedule_type": "daily", "scheduled_time": "24:00"},
            {"schedule_type": "weekly", "day_of_week": ""},
            {"schedule_type": "weekly", "day_of_week": "holiday"},
            {"is_enabled": "true"},
            {"workflow_id": "MISSING"},
        )
        for values in cases:
            with self.subTest(values=values):
                arguments = dict(
                    schedule_id="SCH-BAD", schedule_type="weekly",
                    scheduled_time="10:00", day_of_week="monday",
                    is_enabled=True,
                )
                arguments.update(values)
                self.assertFalse(self.create_schedule(**arguments))
        self.assertEqual(load_workflow_schedules("WF-SCHEDULE", self.database_file), [])

    def test_only_active_workflows_accept_new_schedules_and_ids_are_unique(self):
        self.assertTrue(self.create_schedule())
        self.assertFalse(self.create_schedule())
        self.assertTrue(update_workflow(
            self.admin, "WF-SCHEDULE", "Scheduled workflow", "", "inactive",
            self.database_file,
        ))
        self.assertFalse(self.create_schedule(schedule_id="SCH-2"))

    def test_service_revalidates_administrator_identity_role_and_permission(self):
        for current_user in (
            self.viewer,
            dict(self.admin, is_active=False),
            dict(self.admin, user_id=self.viewer["user_id"]),
            dict(self.admin, username="missing"),
        ):
            self.assertFalse(self.create_schedule(current_user=current_user))
        with patch("workflow_service.user_has_permission", return_value=False):
            self.assertFalse(self.create_schedule())
        with closing(sqlite3.connect(self.database_file)) as connection, connection:
            connection.execute("UPDATE users SET role = 'viewer' WHERE username = 'admin'")
        self.assertFalse(self.create_schedule())
        self.assertEqual(load_workflow_schedules("WF-SCHEDULE", self.database_file), [])

    def test_schedule_status_is_scoped_terminal_safe_and_requires_active_workflow(self):
        self.assertTrue(self.create_schedule(is_enabled=False))
        self.assertTrue(set_workflow_schedule_enabled(
            self.admin, " wf-schedule ", " sch-1 ", True, self.database_file,
        ))
        self.assertFalse(set_workflow_schedule_enabled(
            self.admin, "WF-SCHEDULE", "SCH-1", True, self.database_file,
        ))
        self.assertFalse(set_workflow_schedule_enabled(
            self.admin, "OTHER", "SCH-1", False, self.database_file,
        ))
        self.assertTrue(update_workflow(
            self.admin, "WF-SCHEDULE", "Scheduled workflow", "", "inactive",
            self.database_file,
        ))
        saved = load_workflow_schedule_by_id("SCH-1", self.database_file)
        self.assertFalse(saved["is_enabled"])
        self.assertFalse(set_workflow_schedule_enabled(
            self.admin, "WF-SCHEDULE", "SCH-1", True, self.database_file,
        ))

    def test_browser_form_creation_display_and_activity_log(self):
        self.sign_in()
        form = self.client.get("/workflows/WF-SCHEDULE/schedules/new")
        self.assertEqual(form.status_code, 200)
        self.assertIn("Automatic background execution is not enabled yet", form.text)
        token = re.search(r'name="csrf_token" value="([^"]+)"', form.text).group(1)
        response = self.client.post(
            "/workflows/WF-SCHEDULE/schedules/new",
            data={
                "csrf_token": token, "schedule_id": " sch-web ",
                "schedule_type": "weekly", "scheduled_time": "14:25",
                "day_of_week": "wednesday", "is_enabled": "true",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "http://testserver/workflows/WF-SCHEDULE")
        self.assertIn("schedule SCH-WEB was created", self.log.call_args.args[0])
        page = self.client.get(response.headers["location"])
        self.assertIn("Workflow schedules", page.text)
        self.assertIn("Every Wednesday at 14:25", page.text)
        self.assertIn("Status: Enabled", page.text)
        self.assertIn("Schedules store future run-eligibility rules", page.text)

    def test_browser_validation_preserves_values_and_errors_are_safe(self):
        self.sign_in()
        token = self.csrf_token()
        response = self.client.post(
            "/workflows/WF-SCHEDULE/schedules/new",
            data={
                "csrf_token": token, "schedule_id": "SCH-BAD",
                "schedule_type": "weekly", "scheduled_time": "invalid",
                "day_of_week": "friday", "is_enabled": "true",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('value="SCH-BAD"', response.text)
        self.assertIn('value="friday" selected', response.text)
        with patch("web_app.create_workflow_schedule", side_effect=sqlite3.OperationalError("secret.db")):
            response = self.client.post(
                "/workflows/WF-SCHEDULE/schedules/new",
                data={"csrf_token": token, "schedule_id": "SCH-X", "schedule_type": "manual"},
            )
            self.assertEqual(response.status_code, 500)
            self.assertNotIn("secret.db", response.text)

    def test_browser_creation_requires_session_permission_and_current_csrf(self):
        url = "/workflows/WF-SCHEDULE/schedules/new"
        self.assertEqual(self.client.get(url, follow_redirects=False).status_code, 303)
        self.assertEqual(self.client.post(url, data={}, follow_redirects=False).status_code, 303)
        self.sign_in("viewer")
        self.assertEqual(self.client.get(url).status_code, 403)
        with patch("web_app.create_workflow_schedule") as service:
            self.assertEqual(self.client.post(url, data={"csrf_token": "bad"}).status_code, 403)
            service.assert_not_called()
        self.sign_in()
        with patch("web_app.create_workflow_schedule") as service:
            self.assertEqual(self.client.post(url, data={"csrf_token": "bad"}).status_code, 403)
            service.assert_not_called()
        self.assertIn("CSRF validation failed", self.log.call_args.args[0])

    def test_browser_status_update_is_protected_and_logged(self):
        self.assertTrue(self.create_schedule())
        url = "/workflows/WF-SCHEDULE/schedules/SCH-1/status"
        self.sign_in()
        token = self.csrf_token()
        response = self.client.post(
            url, data={"csrf_token": token, "is_enabled": "false"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        self.assertIn("was disabled", self.log.call_args.args[0])
        self.assertFalse(load_workflow_schedule_by_id("SCH-1", self.database_file)["is_enabled"])
        self.assertEqual(self.client.post(
            url, data={"csrf_token": token, "is_enabled": "unknown"},
        ).status_code, 400)
        self.client.cookies.clear()
        self.sign_in("viewer")
        self.assertEqual(self.client.post(
            url, data={"csrf_token": "bad", "is_enabled": "true"},
        ).status_code, 403)

    def test_deactivation_disables_all_schedules_atomically(self):
        self.assertTrue(self.create_schedule("SCH-1"))
        self.assertTrue(self.create_schedule("SCH-2", "weekly", "10:00", "monday"))
        before = load_workflow_schedules("WF-SCHEDULE", self.database_file)
        self.assertTrue(all(item["is_enabled"] for item in before))
        self.assertTrue(update_workflow(
            self.admin, "WF-SCHEDULE", "Scheduled workflow", "", "draft",
            self.database_file,
        ))
        after = load_workflow_schedules("WF-SCHEDULE", self.database_file)
        self.assertTrue(all(not item["is_enabled"] for item in after))
        self.assertTrue(all(item["updated_at"] != item["created_at"] for item in after))
