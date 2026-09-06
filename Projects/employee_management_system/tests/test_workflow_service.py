import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    load_user_account_by_username,
    load_workflows_from_database,
    update_user_account_active_status,
)
from user_service import register_user_account
from workflow_service import create_workflow


class TestWorkflowService(unittest.TestCase):
    def test_administrator_can_create_normalized_draft_workflow(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            user_created = register_user_account(
                "WorkflowAdmin",
                "SecurePassword123!",
                "admin",
                database_file,
            )
            administrator = load_user_account_by_username(
                "WorkflowAdmin",
                database_file,
            )

            self.assertTrue(user_created)
            self.assertIsNotNone(administrator)

            if administrator is None:
                self.fail(
                    "The workflow administrator was not found."
                )

            workflow_created = create_workflow(
                administrator,
                " wf-000001 ",
                " New employee onboarding ",
                " Coordinate onboarding tasks. ",
                " draft ",
                database_file,
            )
            workflows = load_workflows_from_database(
                database_file,
            )

            self.assertTrue(workflow_created)
            self.assertEqual(len(workflows), 1)

            workflow = workflows[0]

            self.assertEqual(
                workflow["workflow_id"],
                "WF-000001",
            )
            self.assertEqual(
                workflow["name"],
                "New employee onboarding",
            )
            self.assertEqual(
                workflow["description"],
                "Coordinate onboarding tasks.",
            )
            self.assertEqual(
                workflow["status"],
                "draft",
            )
            self.assertEqual(
                workflow["created_by_user_id"],
                administrator["user_id"],
            )
            self.assertEqual(
                workflow["created_at"],
                workflow["updated_at"],
            )
            self.assertTrue(workflow["created_at"])

    def test_viewer_cannot_create_workflow(self):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            user_created = register_user_account(
                "WorkflowViewer",
                "SecurePassword123!",
                "viewer",
                database_file,
            )
            viewer = load_user_account_by_username(
                "WorkflowViewer",
                database_file,
            )

            self.assertTrue(user_created)
            self.assertIsNotNone(viewer)

            if viewer is None:
                self.fail("The workflow viewer was not found.")

            workflow_created = create_workflow(
                viewer,
                "WF-000002",
                "Blocked workflow",
                "",
                "draft",
                database_file,
            )
            workflows = load_workflows_from_database(
                database_file,
            )

            self.assertFalse(workflow_created)
            self.assertEqual(workflows, [])

    def test_create_workflow_rejects_invalid_input(self):
        invalid_cases = [
            (
                "blank workflow ID",
                "   ",
                "Valid workflow name",
                "draft",
            ),
            (
                "blank workflow name",
                "WF-000003",
                "   ",
                "draft",
            ),
            (
                "unknown workflow status",
                "WF-000003",
                "Valid workflow name",
                "unknown",
            ),
            (
                "blank workflow status",
                "WF-000003",
                "Valid workflow name",
                "   ",
            ),
        ]

        for (
            case_name,
            workflow_id,
            name,
            status,
        ) in invalid_cases:
            with self.subTest(case=case_name):
                with TemporaryDirectory() as temporary_directory:
                    database_file = (
                        Path(temporary_directory)
                        / "employees.db"
                    )

                    user_created = register_user_account(
                        "WorkflowAdmin",
                        "SecurePassword123!",
                        "admin",
                        database_file,
                    )
                    administrator = (
                        load_user_account_by_username(
                            "WorkflowAdmin",
                            database_file,
                        )
                    )

                    self.assertTrue(user_created)
                    self.assertIsNotNone(administrator)

                    if administrator is None:
                        self.fail(
                            "The workflow administrator was not found."
                        )

                    workflow_created = create_workflow(
                        administrator,
                        workflow_id,
                        name,
                        "",
                        status,
                        database_file,
                    )
                    workflows = load_workflows_from_database(
                        database_file,
                    )

                    self.assertFalse(workflow_created)
                    self.assertEqual(workflows, [])

    def test_deactivated_administrator_cannot_create_workflow(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            user_created = register_user_account(
                "WorkflowAdmin",
                "SecurePassword123!",
                "admin",
                database_file,
            )
            administrator = load_user_account_by_username(
                "WorkflowAdmin",
                database_file,
            )
            account_deactivated = (
                update_user_account_active_status(
                    "WorkflowAdmin",
                    False,
                    database_file,
                )
            )

            self.assertTrue(user_created)
            self.assertIsNotNone(administrator)
            self.assertTrue(account_deactivated)

            if administrator is None:
                self.fail(
                    "The workflow administrator was not found."
                )

            workflow_created = create_workflow(
                administrator,
                "WF-000004",
                "Blocked deactivated workflow",
                "",
                "draft",
                database_file,
            )
            workflows = load_workflows_from_database(
                database_file,
            )

            self.assertFalse(workflow_created)
            self.assertEqual(workflows, [])