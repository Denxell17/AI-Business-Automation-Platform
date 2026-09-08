import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from database import insert_user_account, load_user_account_by_username, load_workflow_tasks
from workflow_service import (
    create_workflow, create_workflow_task, remove_workflow_task,
    resequence_workflow_task_list,
    update_workflow, update_workflow_task_details,
)


class TestWorkflowTaskMaintenance(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database_file = Path(directory.name) / "tasks.db"
        insert_user_account("admin", "hash", "admin", self.database_file)
        insert_user_account("viewer", "hash", "viewer", self.database_file)
        self.admin = load_user_account_by_username("admin", self.database_file)
        self.viewer = load_user_account_by_username("viewer", self.database_file)
        self.assertTrue(create_workflow(self.admin, "WF-1", "Workflow", "", "draft", self.database_file))
        for position, task_id in enumerate(("TASK-A", "TASK-B", "TASK-C"), start=1):
            self.assertTrue(create_workflow_task(
                self.admin, task_id, "WF-1", position, task_id, "", "manual", True,
                self.database_file,
            ))

    def test_admin_edits_details_without_changing_identity_or_order(self):
        before = load_workflow_tasks("WF-1", self.database_file)[0]
        self.assertTrue(update_workflow_task_details(
            self.admin, "wf-1", "task-a", " Updated title ", " Updated instructions ", False,
            self.database_file,
        ))
        after = load_workflow_tasks("WF-1", self.database_file)[0]
        self.assertEqual(after["task_id"], before["task_id"])
        self.assertEqual(after["sequence_number"], before["sequence_number"])
        self.assertEqual(after["created_at"], before["created_at"])
        self.assertEqual(after["title"], "Updated title")
        self.assertEqual(after["instructions"], "Updated instructions")
        self.assertFalse(after["is_required"])

    def test_edit_denies_viewer_and_wrong_parent(self):
        self.assertFalse(update_workflow_task_details(
            self.viewer, "WF-1", "TASK-A", "Changed", "", True, self.database_file,
        ))
        self.assertFalse(update_workflow_task_details(
            self.admin, "WF-MISSING", "TASK-A", "Changed", "", True, self.database_file,
        ))

    def test_resequence_atomically_changes_to_contiguous_order(self):
        self.assertTrue(resequence_workflow_task_list(
            self.admin, "WF-1", ["TASK-C", "TASK-A", "TASK-B"], self.database_file,
        ))
        tasks = load_workflow_tasks("WF-1", self.database_file)
        self.assertEqual([task["task_id"] for task in tasks], ["TASK-C", "TASK-A", "TASK-B"])
        self.assertEqual([task["sequence_number"] for task in tasks], [1, 2, 3])

    def test_resequence_rejects_duplicates_or_missing_tasks_without_changes(self):
        before = load_workflow_tasks("WF-1", self.database_file)
        for task_ids in (["TASK-A", "TASK-A", "TASK-C"], ["TASK-A", "TASK-B"]):
            self.assertFalse(resequence_workflow_task_list(self.admin, "WF-1", task_ids, self.database_file))
            self.assertEqual(load_workflow_tasks("WF-1", self.database_file), before)

    def test_empty_workflow_cannot_be_activated_but_task_workflow_can(self):
        self.assertTrue(create_workflow(self.admin, "WF-EMPTY", "Empty", "", "draft", self.database_file))
        self.assertFalse(update_workflow(self.admin, "WF-EMPTY", "Empty", "", "active", self.database_file))
        self.assertTrue(update_workflow(self.admin, "WF-1", "Workflow", "", "active", self.database_file))
        self.assertFalse(create_workflow(self.admin, "WF-ACTIVE", "No task", "", "active", self.database_file))

    def test_admin_deletes_middle_task_and_remaining_tasks_are_contiguous(self):
        before = load_workflow_tasks("WF-1", self.database_file)

        self.assertTrue(remove_workflow_task(
            self.admin, " wf-1 ", " task-b ", self.database_file,
        ))

        after = load_workflow_tasks("WF-1", self.database_file)
        self.assertEqual([task["task_id"] for task in after], ["TASK-A", "TASK-C"])
        self.assertEqual([task["sequence_number"] for task in after], [1, 2])
        self.assertEqual(after[0]["updated_at"], before[0]["updated_at"])
        self.assertNotEqual(after[1]["updated_at"], before[2]["updated_at"])

    def test_delete_denies_viewer_missing_task_and_stale_admin(self):
        before = load_workflow_tasks("WF-1", self.database_file)
        self.assertFalse(remove_workflow_task(
            self.viewer, "WF-1", "TASK-B", self.database_file,
        ))
        self.assertFalse(remove_workflow_task(
            self.admin, "WF-1", "TASK-MISSING", self.database_file,
        ))
        stale_admin = dict(self.admin)
        stale_admin["user_id"] = self.viewer["user_id"]
        self.assertFalse(remove_workflow_task(
            stale_admin, "WF-1", "TASK-B", self.database_file,
        ))
        self.assertEqual(load_workflow_tasks("WF-1", self.database_file), before)

    def test_active_workflow_cannot_lose_its_last_task(self):
        self.assertTrue(create_workflow(
            self.admin, "WF-ACTIVE", "Active", "", "draft", self.database_file,
        ))
        self.assertTrue(create_workflow_task(
            self.admin, "ONLY-TASK", "WF-ACTIVE", 1, "Only task", "",
            "manual", True, self.database_file,
        ))
        self.assertTrue(update_workflow(
            self.admin, "WF-ACTIVE", "Active", "", "active", self.database_file,
        ))

        self.assertFalse(remove_workflow_task(
            self.admin, "WF-ACTIVE", "ONLY-TASK", self.database_file,
        ))
        self.assertEqual(
            [task["task_id"] for task in load_workflow_tasks("WF-ACTIVE", self.database_file)],
            ["ONLY-TASK"],
        )
