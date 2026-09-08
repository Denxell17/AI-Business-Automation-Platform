import re
import unittest
import sqlite3
from unittest.mock import patch
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from database import (
    insert_workflow_task,
    load_user_account_by_username,
    load_workflow_by_id,
)
from user_service import register_user_account
from web_app import create_web_application
from workflow_service import create_workflow, create_workflow_task, update_workflow


class TestWorkflowWebLifecycle(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name) / "employees.db"
        )
        self.application = create_web_application(
            database_file=self.database_file,
            session_secret="workflow-lifecycle-test-secret",
        )
        self.client = TestClient(self.application)
        self.admin_username = "WorkflowAdmin"
        self.admin_password = "SecurePassword123!"
        self.viewer_username = "WorkflowViewer"
        self.viewer_password = "SecurePassword123!"

        register_user_account(
            self.admin_username,
            self.admin_password,
            "admin",
            self.database_file,
        )
        register_user_account(
            self.viewer_username,
            self.viewer_password,
            "viewer",
            self.database_file,
        )

        self.sign_in(self.admin_username, self.admin_password)
        administrator = load_user_account_by_username(
            self.admin_username,
            self.database_file,
        )

        if administrator is None:
            self.fail("Workflow administrator was not created.")

        self.assertTrue(
            create_workflow(
                administrator,
                "WF-WEB-LIFECYCLE",
                "Browser workflow",
                "A workflow used for browser tests.",
                "draft",
                self.database_file,
            )
        )
        self.client.post("/logout")

    def tearDown(self):
        self.client.close()
        self.temporary_directory.cleanup()

    def sign_in(self, username: str, password: str):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    def get_edit_csrf_token(self) -> str:
        response = self.client.get(
            "/workflows/WF-WEB-LIFECYCLE/edit"
        )
        self.assertEqual(response.status_code, 200)
        token_match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"',
            response.text,
        )
        self.assertIsNotNone(token_match)

        if token_match is None:
            self.fail("Workflow-edit form did not contain a CSRF token.")

        return token_match.group(1)

    def get_task_csrf_token(self) -> str:
        response = self.client.get("/workflows/WF-WEB-LIFECYCLE/tasks/new")
        self.assertEqual(response.status_code, 200)
        token_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
        self.assertIsNotNone(token_match)
        if token_match is None:
            self.fail("Task form did not contain a CSRF token.")
        return token_match.group(1)

    def test_administrator_can_create_task_and_is_redirected_to_detail(self):
        self.sign_in(self.admin_username, self.admin_password)
        csrf_token = self.get_task_csrf_token()
        response = self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/tasks/new",
            data={
                "csrf_token": csrf_token,
                "task_id": " task-web-001 ",
                "sequence_number": "2",
                "title": " Confirm documents ",
                "instructions": " Review documents. ",
                "is_required": "true",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        self.assertEqual(response.headers["location"], "http://testserver/workflows/WF-WEB-LIFECYCLE")
        detail = self.client.get("/workflows/WF-WEB-LIFECYCLE")
        self.assertIn("Confirm documents", detail.text)
        self.assertIn("Required", detail.text)

    def create_browser_task(self, task_id, position):
        response = self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/tasks/new",
            data={"csrf_token": self.get_task_csrf_token(), "task_id": task_id,
                  "sequence_number": str(position), "title": task_id,
                  "is_required": "true"}, follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)

    def test_administrator_can_edit_a_task(self):
        self.sign_in(self.admin_username, self.admin_password)
        self.create_browser_task("TASK-EDIT", 1)
        form = self.client.get("/workflows/WF-WEB-LIFECYCLE/tasks/TASK-EDIT/edit")
        token = re.search(r'name="csrf_token" value="([^"]+)"', form.text).group(1)
        response = self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/tasks/TASK-EDIT/edit",
            data={"csrf_token": token, "title": "Edited task", "instructions": "New instructions", "is_required": "false"},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        detail = self.client.get("/workflows/WF-WEB-LIFECYCLE")
        self.assertIn("Edited task", detail.text)
        self.assertIn("Optional", detail.text)

    def test_administrator_can_resequence_tasks(self):
        self.sign_in(self.admin_username, self.admin_password)
        self.create_browser_task("TASK-FIRST", 1)
        self.create_browser_task("TASK-SECOND", 2)
        form = self.client.get("/workflows/WF-WEB-LIFECYCLE/tasks/resequence")
        token = re.search(r'name="csrf_token" value="([^"]+)"', form.text).group(1)
        response = self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/tasks/resequence",
            data={"csrf_token": token, "task_ids": ["TASK-SECOND", "TASK-FIRST"]},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 303)
        detail = self.client.get("/workflows/WF-WEB-LIFECYCLE")
        self.assertLess(detail.text.index("TASK-SECOND"), detail.text.index("TASK-FIRST"))

    def test_administrator_can_start_active_workflow_execution(self):
        self.sign_in(self.admin_username, self.admin_password)
        administrator = load_user_account_by_username(
            self.admin_username, self.database_file,
        )
        self.assertTrue(create_workflow_task(
            administrator, "TASK-RUN", "WF-WEB-LIFECYCLE", 1, "Run task", "",
            "manual", True, self.database_file,
        ))
        self.assertTrue(update_workflow(
            administrator, "WF-WEB-LIFECYCLE", "Browser workflow",
            "A workflow used for browser tests.", "active", self.database_file,
        ))
        detail = self.client.get("/workflows/WF-WEB-LIFECYCLE")
        self.assertIn("Start execution", detail.text)
        token = re.search(r'name="csrf_token" value="([^"]+)"', detail.text).group(1)

        with patch("web_app.log_activity") as log_activity_mock:
            response = self.client.post(
                "/workflows/WF-WEB-LIFECYCLE/executions",
                data={"csrf_token": token}, follow_redirects=False,
            )

        self.assertEqual(response.status_code, 303)
        self.assertIn("was started", log_activity_mock.call_args.args[0])
        updated_detail = self.client.get("/workflows/WF-WEB-LIFECYCLE")
        self.assertIn("Execution history", updated_detail.text)
        self.assertIn("Execution started.", updated_detail.text)

    def test_execution_start_rejects_invalid_csrf_and_viewer(self):
        self.sign_in(self.admin_username, self.admin_password)
        response = self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/executions",
            data={"csrf_token": "invalid"}, follow_redirects=False,
        )
        self.assertEqual(response.status_code, 403)
        self.client.post("/logout")
        self.sign_in(self.viewer_username, self.viewer_password)
        self.assertNotIn("Start execution", self.client.get(
            "/workflows/WF-WEB-LIFECYCLE"
        ).text)
        self.assertEqual(self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/executions",
            data={"csrf_token": "invalid"}, follow_redirects=False,
        ).status_code, 403)

    def test_administrator_confirms_and_deletes_task(self):
        self.sign_in(self.admin_username, self.admin_password)
        self.create_browser_task("TASK-DELETE", 1)
        self.create_browser_task("TASK-REMAINS", 2)
        form = self.client.get(
            "/workflows/WF-WEB-LIFECYCLE/tasks/TASK-DELETE/delete"
        )
        self.assertEqual(form.status_code, 200)
        self.assertIn("This cannot be undone", form.text)
        token = re.search(r'name="csrf_token" value="([^"]+)"', form.text).group(1)

        with patch("web_app.log_activity") as log_activity_mock:
            response = self.client.post(
                "/workflows/WF-WEB-LIFECYCLE/tasks/TASK-DELETE/delete",
                data={"csrf_token": token}, follow_redirects=False,
            )

        self.assertEqual(response.status_code, 303)
        self.assertIn("TASK-DELETE", log_activity_mock.call_args.args[0])
        self.assertIn("resequence", log_activity_mock.call_args.args[0])
        detail = self.client.get("/workflows/WF-WEB-LIFECYCLE")
        self.assertNotIn("TASK-DELETE", detail.text)
        self.assertIn("TASK-REMAINS", detail.text)

    def test_task_delete_rejects_invalid_csrf_and_viewer(self):
        self.sign_in(self.admin_username, self.admin_password)
        self.create_browser_task("TASK-PROTECTED", 1)
        response = self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/tasks/TASK-PROTECTED/delete",
            data={"csrf_token": "invalid"}, follow_redirects=False,
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("TASK-PROTECTED", self.client.get(
            "/workflows/WF-WEB-LIFECYCLE"
        ).text)

        self.client.post("/logout")
        self.sign_in(self.viewer_username, self.viewer_password)
        self.assertEqual(self.client.get(
            "/workflows/WF-WEB-LIFECYCLE/tasks/TASK-PROTECTED/delete"
        ).status_code, 403)
        self.assertEqual(self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/tasks/TASK-PROTECTED/delete",
            data={"csrf_token": "invalid"}, follow_redirects=False,
        ).status_code, 403)

    def test_viewer_cannot_edit_or_resequence_tasks(self):
        self.sign_in(self.viewer_username, self.viewer_password)
        self.assertEqual(self.client.get("/workflows/WF-WEB-LIFECYCLE/tasks/TASK/edit").status_code, 403)
        self.assertEqual(self.client.get("/workflows/WF-WEB-LIFECYCLE/tasks/resequence").status_code, 403)

    def test_task_form_preserves_values_after_validation_failure(self):
        self.sign_in(self.admin_username, self.admin_password)
        response = self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/tasks/new",
            data={
                "csrf_token": self.get_task_csrf_token(),
                "task_id": "TASK-BAD",
                "sequence_number": "not-a-number",
                "title": "Retained task title",
                "instructions": "Retained instructions",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Task could not be created.", response.text)
        self.assertIn('value="TASK-BAD"', response.text)
        self.assertIn('value="not-a-number"', response.text)
        self.assertIn("Retained task title", response.text)
        self.assertIn("Retained instructions", response.text)

    def test_viewer_cannot_access_or_submit_task_form(self):
        self.sign_in(self.viewer_username, self.viewer_password)
        get_response = self.client.get("/workflows/WF-WEB-LIFECYCLE/tasks/new")
        post_response = self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/tasks/new",
            data={"csrf_token": "invalid"},
        )
        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(get_response.text, "Access denied.")
        self.assertEqual(post_response.text, "Access denied.")

    def test_task_form_rejects_invalid_csrf_before_service_call(self):
        self.sign_in(self.admin_username, self.admin_password)
        with patch("web_app.create_workflow_task") as create_task:
            response = self.client.post(
                "/workflows/WF-WEB-LIFECYCLE/tasks/new",
                data={"csrf_token": "invalid"},
            )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.text, "Your form could not be verified.")
        create_task.assert_not_called()

    def test_task_form_rejects_invalid_required_value_safely(self):
        self.sign_in(self.admin_username, self.admin_password)
        response = self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/tasks/new",
            data={
                "csrf_token": self.get_task_csrf_token(),
                "task_id": "TASK-BAD-REQUIRED",
                "sequence_number": "1",
                "title": "Invalid required value",
                "is_required": "maybe",
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Task could not be created.", response.text)

    def test_task_form_returns_safe_message_for_service_database_error(self):
        self.sign_in(self.admin_username, self.admin_password)
        with patch("web_app.create_workflow_task", side_effect=sqlite3.OperationalError("private details")):
            response = self.client.post(
                "/workflows/WF-WEB-LIFECYCLE/tasks/new",
                data={
                    "csrf_token": self.get_task_csrf_token(),
                    "task_id": "TASK-ERROR",
                    "sequence_number": "1",
                    "title": "Database error task",
                    "is_required": "true",
                },
            )
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.text, "Workflow records could not be loaded.")

    def test_viewer_can_view_detail_but_not_edit(self):
        self.sign_in(self.viewer_username, self.viewer_password)

        detail_response = self.client.get(
            "/workflows/WF-WEB-LIFECYCLE"
        )
        edit_response = self.client.get(
            "/workflows/WF-WEB-LIFECYCLE/edit"
        )

        self.assertEqual(detail_response.status_code, 200)
        self.assertIn("Browser workflow", detail_response.text)
        self.assertNotIn("Edit workflow", detail_response.text)
        self.assertEqual(edit_response.status_code, 403)
        self.assertEqual(edit_response.text, "Access denied.")

    def test_roles_can_read_ordered_tasks_with_escaped_content(self):
        for sequence in (3, 1):
            self.assertTrue(insert_workflow_task({
                "task_id": f"TASK-{sequence}",
                "workflow_id": "WF-WEB-LIFECYCLE",
                "sequence_number": sequence,
                "title": f"Step {sequence} <script>alert(1)</script>",
                "instructions": "<b>Review documents</b>" if sequence == 1 else "",
                "task_type": "manual",
                "is_required": sequence == 1,
                "created_at": "2026-09-07T00:00:00+00:00",
                "updated_at": "2026-09-07T00:00:00+00:00",
            }, self.database_file))
        for username, password in (
            (self.admin_username, self.admin_password),
            (self.viewer_username, self.viewer_password),
        ):
            with self.subTest(username=username):
                self.sign_in(username, password)
                response = self.client.get("/workflows/WF-WEB-LIFECYCLE")
                self.assertEqual(response.status_code, 200)
                self.assertLess(response.text.index("Step 1"), response.text.index("Step 3"))
                self.assertIn('value="3"', response.text)
                self.assertIn("Required", response.text)
                self.assertIn("Optional", response.text)
                self.assertIn("No instructions provided.", response.text)
                self.assertIn("&lt;script&gt;", response.text)
                self.assertIn("&lt;b&gt;Review documents&lt;/b&gt;", response.text)
                self.assertNotIn("<script>alert(1)</script>", response.text)
                self.client.post("/logout")

    def test_empty_task_message(self):
        self.sign_in(self.viewer_username, self.viewer_password)
        response = self.client.get("/workflows/WF-WEB-LIFECYCLE")
        self.assertEqual(response.status_code, 200)
        self.assertIn("No tasks have been added to this workflow yet.", response.text)

    def test_anonymous_request_does_not_load_tasks(self):
        with patch("web_app.load_workflow_tasks") as load_tasks:
            response = self.client.get(
                "/workflows/WF-WEB-LIFECYCLE", follow_redirects=False,
            )
        self.assertEqual(response.status_code, 303)
        load_tasks.assert_not_called()

    def test_task_storage_error_returns_safe_response(self):
        self.sign_in(self.viewer_username, self.viewer_password)
        with patch("web_app.load_workflow_tasks", side_effect=sqlite3.OperationalError("private details")):
            response = self.client.get("/workflows/WF-WEB-LIFECYCLE")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.text, "Workflow records could not be loaded.")

    def test_administrator_can_edit_workflow(self):
        self.sign_in(self.admin_username, self.admin_password)
        csrf_token = self.get_edit_csrf_token()

        response = self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/edit",
            data={
                "csrf_token": csrf_token,
                "name": "Updated browser workflow",
                "description": "Updated in the browser.",
                "status": "inactive",
            },
            follow_redirects=False,
        )
        workflow = load_workflow_by_id(
            "WF-WEB-LIFECYCLE",
            self.database_file,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/workflows/WF-WEB-LIFECYCLE",
        )
        self.assertIsNotNone(workflow)

        if workflow is None:
            self.fail("The updated workflow was not loaded.")

        self.assertEqual(workflow["name"], "Updated browser workflow")
        self.assertEqual(workflow["status"], "inactive")

    def test_edit_rejects_invalid_csrf_token(self):
        self.sign_in(self.admin_username, self.admin_password)

        response = self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/edit",
            data={
                "csrf_token": "invalid-csrf-token",
                "name": "Forged update",
                "description": "This must not be saved.",
                "status": "inactive",
            },
        )
        workflow = load_workflow_by_id(
            "WF-WEB-LIFECYCLE",
            self.database_file,
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.text,
            "Your form could not be verified.",
        )
        self.assertIsNotNone(workflow)

        if workflow is None:
            self.fail("The saved workflow was not loaded.")

        self.assertEqual(workflow["name"], "Browser workflow")

    def test_missing_workflow_returns_not_found(self):
        self.sign_in(self.viewer_username, self.viewer_password)

        response = self.client.get("/workflows/WF-MISSING")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.text, "Workflow not found.")

    def test_viewer_can_filter_workflow_directory_by_status(self):
        self.sign_in(self.viewer_username, self.viewer_password)

        response = self.client.get("/workflows?status=draft")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Browser workflow", response.text)
        self.assertRegex(
            response.text,
            r'value="draft"\s+selected',
        )

    def test_workflow_directory_rejects_unknown_status_filter(self):
        self.sign_in(self.viewer_username, self.viewer_password)

        response = self.client.get("/workflows?status=unknown")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.text,
            "Workflow status filter is invalid.",
        )
