import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    load_user_account_by_username,
    load_workflow_by_id,
)
from user_service import register_user_account
from workflow_service import (
    create_workflow,
    update_workflow,
)


class TestWorkflowLifecycle(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name) / "employees.db"
        )
        register_user_account(
            "WorkflowAdmin",
            "SecurePassword123!",
            "admin",
            self.database_file,
        )
        register_user_account(
            "WorkflowViewer",
            "SecurePassword123!",
            "viewer",
            self.database_file,
        )
        self.administrator = load_user_account_by_username(
            "WorkflowAdmin",
            self.database_file,
        )
        self.viewer = load_user_account_by_username(
            "WorkflowViewer",
            self.database_file,
        )

        if self.administrator is None or self.viewer is None:
            self.fail("Workflow test accounts were not created.")

        workflow_created = create_workflow(
            self.administrator,
            "WF-LIFECYCLE-001",
            "Initial workflow",
            "Original description.",
            "draft",
            self.database_file,
        )

        self.assertTrue(workflow_created)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_load_workflow_by_id_returns_saved_record(self):
        workflow = load_workflow_by_id(
            "WF-LIFECYCLE-001",
            self.database_file,
        )

        self.assertIsNotNone(workflow)

        if workflow is None:
            self.fail("The saved workflow was not loaded.")

        self.assertEqual(workflow["name"], "Initial workflow")
        self.assertEqual(workflow["status"], "draft")

    def test_administrator_can_update_existing_workflow(self):
        before_update = load_workflow_by_id(
            "WF-LIFECYCLE-001",
            self.database_file,
        )

        workflow_updated = update_workflow(
            self.administrator,
            " wf-lifecycle-001 ",
            " Updated workflow ",
            " Updated description. ",
            " ACTIVE ",
            self.database_file,
        )
        after_update = load_workflow_by_id(
            "WF-LIFECYCLE-001",
            self.database_file,
        )

        self.assertIsNotNone(before_update)
        self.assertTrue(workflow_updated)
        self.assertIsNotNone(after_update)

        if before_update is None or after_update is None:
            self.fail("The updated workflow was not loaded.")

        self.assertEqual(after_update["name"], "Updated workflow")
        self.assertEqual(
            after_update["description"],
            "Updated description.",
        )
        self.assertEqual(after_update["status"], "active")
        self.assertEqual(
            after_update["created_at"],
            before_update["created_at"],
        )
        self.assertEqual(
            after_update["created_by_user_id"],
            before_update["created_by_user_id"],
        )

    def test_viewer_cannot_update_workflow(self):
        workflow_updated = update_workflow(
            self.viewer,
            "WF-LIFECYCLE-001",
            "Viewer update",
            "This must not be saved.",
            "inactive",
            self.database_file,
        )
        workflow = load_workflow_by_id(
            "WF-LIFECYCLE-001",
            self.database_file,
        )

        self.assertFalse(workflow_updated)
        self.assertIsNotNone(workflow)

        if workflow is None:
            self.fail("The saved workflow was not loaded.")

        self.assertEqual(workflow["name"], "Initial workflow")
        self.assertEqual(workflow["status"], "draft")

    def test_update_rejects_unknown_status(self):
        workflow_updated = update_workflow(
            self.administrator,
            "WF-LIFECYCLE-001",
            "Initial workflow",
            "Original description.",
            "unknown",
            self.database_file,
        )
        workflow = load_workflow_by_id(
            "WF-LIFECYCLE-001",
            self.database_file,
        )

        self.assertFalse(workflow_updated)
        self.assertIsNotNone(workflow)

        if workflow is None:
            self.fail("The saved workflow was not loaded.")

        self.assertEqual(workflow["status"], "draft")
