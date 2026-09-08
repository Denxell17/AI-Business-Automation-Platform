import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    insert_user_account,
    load_user_account_by_username,
    load_workflow_executions,
)
from workflow_service import (
    create_workflow,
    create_workflow_task,
    start_workflow_execution,
    finish_workflow_execution_record,
    update_workflow,
)


class TestWorkflowExecutions(unittest.TestCase):
    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.database_file = Path(directory.name) / "executions.db"
        insert_user_account("admin", "hash", "admin", self.database_file)
        insert_user_account("viewer", "hash", "viewer", self.database_file)
        self.admin = load_user_account_by_username("admin", self.database_file)
        self.viewer = load_user_account_by_username("viewer", self.database_file)
        self.assertTrue(create_workflow(
            self.admin, "WF-RUN", "Run workflow", "", "draft", self.database_file,
        ))
        self.assertTrue(create_workflow_task(
            self.admin, "TASK-RUN", "WF-RUN", 1, "Run task", "", "manual", True,
            self.database_file,
        ))

    def test_admin_starts_active_workflow_with_immutable_snapshot(self):
        self.assertTrue(update_workflow(
            self.admin, "WF-RUN", "Run workflow", "", "active", self.database_file,
        ))

        execution = start_workflow_execution(self.admin, " wf-run ", self.database_file)

        self.assertIsNotNone(execution)
        self.assertTrue(execution["execution_id"].startswith("WFE-"))
        self.assertEqual(execution["workflow_name"], "Run workflow")
        self.assertEqual(execution["status"], "running")
        self.assertIsNone(execution["finished_at"])
        self.assertEqual(execution["result_summary"], "Execution started.")
        self.assertEqual(load_workflow_executions("WF-RUN", self.database_file), [execution])

    def test_draft_workflow_and_unauthorized_or_stale_users_are_rejected(self):
        self.assertIsNone(start_workflow_execution(
            self.admin, "WF-RUN", self.database_file,
        ))
        self.assertTrue(update_workflow(
            self.admin, "WF-RUN", "Run workflow", "", "active", self.database_file,
        ))
        self.assertIsNone(start_workflow_execution(
            self.viewer, "WF-RUN", self.database_file,
        ))
        stale_admin = dict(self.admin)
        stale_admin["user_id"] = self.viewer["user_id"]
        self.assertIsNone(start_workflow_execution(
            stale_admin, "WF-RUN", self.database_file,
        ))
        self.assertEqual(load_workflow_executions("WF-RUN", self.database_file), [])

    def test_execution_loading_is_scoped_and_newest_first(self):
        self.assertTrue(update_workflow(
            self.admin, "WF-RUN", "Run workflow", "", "active", self.database_file,
        ))
        first = start_workflow_execution(self.admin, "WF-RUN", self.database_file)
        second = start_workflow_execution(self.admin, "WF-RUN", self.database_file)

        executions = load_workflow_executions("WF-RUN", self.database_file)
        self.assertEqual({item["execution_id"] for item in executions}, {
            first["execution_id"], second["execution_id"],
        })
        self.assertEqual(load_workflow_executions("MISSING", self.database_file), [])

    def test_admin_can_complete_once_but_viewer_cannot_finish_execution(self):
        self.assertTrue(update_workflow(
            self.admin, "WF-RUN", "Run workflow", "", "active", self.database_file,
        ))
        execution = start_workflow_execution(self.admin, "WF-RUN", self.database_file)
        self.assertFalse(finish_workflow_execution_record(
            self.viewer, execution["execution_id"], "completed", "Done", self.database_file,
        ))
        self.assertTrue(finish_workflow_execution_record(
            self.admin, execution["execution_id"], "completed", "Done", self.database_file,
        ))
        self.assertFalse(finish_workflow_execution_record(
            self.admin, execution["execution_id"], "failed", "Late change", self.database_file,
        ))
        saved = load_workflow_executions("WF-RUN", self.database_file)[0]
        self.assertEqual(saved["status"], "completed")
        self.assertEqual(saved["result_summary"], "Done")
        self.assertIsNotNone(saved["finished_at"])
