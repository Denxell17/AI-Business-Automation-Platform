import re
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from database import (
    load_user_account_by_username,
    load_workflow_by_id,
)
from user_service import register_user_account
from web_app import create_web_application
from workflow_service import create_workflow


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

    def test_administrator_can_edit_workflow(self):
        self.sign_in(self.admin_username, self.admin_password)
        csrf_token = self.get_edit_csrf_token()

        response = self.client.post(
            "/workflows/WF-WEB-LIFECYCLE/edit",
            data={
                "csrf_token": csrf_token,
                "name": "Updated browser workflow",
                "description": "Updated in the browser.",
                "status": "active",
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
        self.assertEqual(workflow["status"], "active")

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
