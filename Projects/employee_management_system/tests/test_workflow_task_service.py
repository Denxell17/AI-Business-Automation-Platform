import unittest
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    get_database_connection,
    insert_user_account,
    load_user_account_by_username,
    load_workflow_tasks,
    update_user_account_active_status,
)
from workflow_service import create_workflow, create_workflow_task


class TestWorkflowTaskService(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database_file = Path(directory.name) / "tasks.db"
        for username, role in (("Admin", "admin"), ("Viewer", "viewer")):
            self.assertTrue(insert_user_account(
                username, "test-hash", role, self.database_file,
            ))
        self.admin = load_user_account_by_username("Admin", self.database_file)
        self.viewer = load_user_account_by_username("Viewer", self.database_file)
        self.assertTrue(create_workflow(
            self.admin, "WF-001", "Onboarding", "", "draft", self.database_file,
        ))

    def create_task(self, user=None, **changes):
        values = {
            "task_id": " wft-001 ",
            "workflow_id": " wf-001 ",
            "sequence_number": 1,
            "title": " Confirm documents ",
            "instructions": " Review employee documents. ",
            "task_type": " MANUAL ",
            "is_required": True,
        }
        values.update(changes)
        return create_workflow_task(
            self.admin if user is None else user,
            database_file=self.database_file, **values,
        )

    def test_admin_creates_normalized_task_with_utc_timestamps(self):
        self.assertTrue(self.create_task())
        tasks = load_workflow_tasks("WF-001", self.database_file)
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task["task_id"], "WFT-001")
        self.assertEqual(task["workflow_id"], "WF-001")
        self.assertEqual(task["title"], "Confirm documents")
        self.assertEqual(task["instructions"], "Review employee documents.")
        self.assertEqual(task["task_type"], "manual")
        self.assertEqual(task["sequence_number"], 1)
        self.assertIs(task["is_required"], True)
        self.assertEqual(task["created_at"], task["updated_at"])
        self.assertEqual(datetime.fromisoformat(task["created_at"]).utcoffset(), timedelta(0))

    def test_optional_task_allows_empty_instructions(self):
        self.assertTrue(self.create_task(is_required=False, instructions="   "))
        task = load_workflow_tasks("WF-001", self.database_file)[0]
        self.assertIs(task["is_required"], False)
        self.assertEqual(task["instructions"], "")

    def test_invalid_inputs_leave_no_records(self):
        cases = [
            {"task_id": " "}, {"workflow_id": " "}, {"title": " "},
            {"workflow_id": "MISSING"}, {"task_type": "email"},
            {"sequence_number": 0}, {"sequence_number": -1},
            {"sequence_number": True}, {"sequence_number": 1.5},
            {"sequence_number": "1"}, {"sequence_number": 2 ** 63},
            {"is_required": 1}, {"is_required": "false"},
        ]
        cases.extend({field: None} for field in (
            "task_id", "workflow_id", "title", "instructions", "task_type",
        ))
        for changes in cases:
            with self.subTest(changes=changes):
                self.assertFalse(self.create_task(**changes))
                self.assertEqual(load_workflow_tasks("WF-001", self.database_file), [])

    def test_viewer_and_forged_session_role_are_denied(self):
        for user in (self.viewer, dict(self.viewer, role="admin")):
            self.assertFalse(self.create_task(user=user))
        self.assertEqual(load_workflow_tasks("WF-001", self.database_file), [])

    def test_inactive_or_mismatched_session_is_denied(self):
        for user in (
            dict(self.admin, is_active=False),
            dict(self.admin, user_id=self.admin["user_id"] + 100),
            dict(self.admin, username="missing"),
        ):
            self.assertFalse(self.create_task(user=user))
        self.assertEqual(load_workflow_tasks("WF-001", self.database_file), [])

    def test_deactivated_saved_account_is_denied(self):
        self.assertTrue(update_user_account_active_status("Admin", False, self.database_file))
        self.assertFalse(self.create_task())
        self.assertEqual(load_workflow_tasks("WF-001", self.database_file), [])

    def test_demoted_saved_account_is_denied(self):
        connection = get_database_connection(self.database_file)
        try:
            connection.execute("UPDATE users SET role = 'viewer' WHERE username = ?", ("Admin",))
            connection.commit()
        finally:
            connection.close()
        self.assertFalse(self.create_task())
        self.assertEqual(load_workflow_tasks("WF-001", self.database_file), [])

    def test_duplicate_id_or_position_preserves_saved_task(self):
        self.assertTrue(self.create_task())
        before = load_workflow_tasks("WF-001", self.database_file)
        self.assertFalse(self.create_task(sequence_number=2))
        self.assertFalse(self.create_task(task_id="WFT-002"))
        self.assertEqual(load_workflow_tasks("WF-001", self.database_file), before)

    def test_same_sequence_allowed_in_another_workflow(self):
        self.assertTrue(create_workflow(
            self.admin, "WF-002", "Other", "", "draft", self.database_file,
        ))
        self.assertTrue(self.create_task())
        self.assertTrue(self.create_task(task_id="WFT-002", workflow_id="WF-002"))
        self.assertEqual(len(load_workflow_tasks("WF-001", self.database_file)), 1)
        self.assertEqual(len(load_workflow_tasks("WF-002", self.database_file)), 1)
