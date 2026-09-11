import re
import sqlite3
import unittest
from html import unescape
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

from agent_template_service import (
    create_agent_template,
    update_agent_template,
)
from database import (
    load_agent_template_by_id,
    load_user_account_by_username,
)
from user_service import register_user_account
from web_app import create_web_application


class TestAgentTemplateWebLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = TemporaryDirectory()
        cls.database_file = (
            Path(cls.temporary_directory.name)
            / "agent-template-web-lifecycle.db"
        )

        cls.admin_username = "AgentLifecycleAdmin"
        cls.admin_password = "SecureAdminPassword123!"

        cls.viewer_username = "AgentLifecycleViewer"
        cls.viewer_password = "SecureViewerPassword123!"

        admin_created = register_user_account(
            cls.admin_username,
            cls.admin_password,
            "admin",
            cls.database_file,
        )
        viewer_created = register_user_account(
            cls.viewer_username,
            cls.viewer_password,
            "viewer",
            cls.database_file,
        )

        if not admin_created or not viewer_created:
            raise RuntimeError(
                "Agent-template lifecycle users could not be created."
            )

        cls.administrator = load_user_account_by_username(
            cls.admin_username,
            cls.database_file,
        )
        cls.viewer = load_user_account_by_username(
            cls.viewer_username,
            cls.database_file,
        )

        if cls.administrator is None or cls.viewer is None:
            raise RuntimeError(
                "Agent-template lifecycle users could not be loaded."
            )

    @classmethod
    def tearDownClass(cls):
        cls.temporary_directory.cleanup()

    def setUp(self):
        application = create_web_application(
            database_file=self.database_file,
            session_secret=(
                "day-146-agent-template-web-lifecycle"
            ),
        )
        self.client = TestClient(application)

        self.agent_template_id = (
            f"AGENT-{uuid4().hex[:12].upper()}"
        )
        self.original_name = "Lifecycle Support Agent"
        self.original_description = (
            "Supports the Day 146 lifecycle tests."
        )
        self.original_system_prompt = (
            "Answer clearly. <script>alert('x')</script>"
        )
        self.original_model_name = "gpt-5.6-terra"

        created = create_agent_template(
            self.administrator,
            self.agent_template_id,
            self.original_name,
            self.original_description,
            self.original_system_prompt,
            self.original_model_name,
            "draft",
            self.database_file,
        )
        self.assertTrue(created)

    def tearDown(self):
        self.client.close()

    def sign_in_as_admin(self):
        return self.client.post(
            "/login",
            data={
                "username": self.admin_username,
                "password": self.admin_password,
            },
            follow_redirects=False,
        )

    def sign_in_as_viewer(self):
        return self.client.post(
            "/login",
            data={
                "username": self.viewer_username,
                "password": self.viewer_password,
            },
            follow_redirects=False,
        )

    def get_edit_csrf_token(self) -> str:
        response = self.client.get(
            f"/agent-templates/"
            f"{self.agent_template_id}/edit"
        )

        self.assertEqual(response.status_code, 200)

        token_match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"',
            response.text,
        )
        self.assertIsNotNone(token_match)

        if token_match is None:
            self.fail(
                "Agent-template edit form did not contain "
                "a CSRF token."
            )

        return token_match.group(1)

    def test_detail_redirects_unauthenticated_user(self):
        response = self.client.get(
            f"/agent-templates/{self.agent_template_id}",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )

    def test_administrator_can_view_protected_detail(
        self,
    ):
        self.sign_in_as_admin()

        response = self.client.get(
            f"/agent-templates/{self.agent_template_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.original_name, response.text)
        self.assertIn(
            self.original_description,
            response.text,
        )
        self.assertIn(
            self.original_model_name,
            response.text,
        )
        self.assertIn("Draft", response.text)
        self.assertIn("System prompt", response.text)
        self.assertIn("Answer clearly.", response.text)
        self.assertIn("&lt;script&gt;", response.text)
        self.assertNotIn("<script>alert", response.text)
        self.assertIn(
            "Edit agent template",
            response.text,
        )

    def test_viewer_can_view_detail_without_edit_action(
        self,
    ):
        self.sign_in_as_viewer()

        response = self.client.get(
            f"/agent-templates/{self.agent_template_id}"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.original_name, response.text)
        self.assertIn("Answer clearly.", response.text)
        self.assertNotIn(
            "Edit agent template",
            response.text,
        )

    def test_missing_template_detail_returns_not_found(
        self,
    ):
        self.sign_in_as_viewer()

        response = self.client.get(
            "/agent-templates/AGENT-MISSING"
        )

        self.assertEqual(response.status_code, 404)
        self.assertIn(
            "The requested agent template was not found.",
            response.text,
        )

    @patch(
        "web_app.load_agent_template_by_id",
        side_effect=sqlite3.Error(
            "Sensitive detail database error."
        ),
    )
    def test_detail_database_error_is_safe(
        self,
        mock_load_agent_template,
    ):
        self.sign_in_as_admin()

        response = self.client.get(
            f"/agent-templates/{self.agent_template_id}"
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "The agent template could not be loaded.",
            response.text,
        )
        self.assertNotIn(
            "Sensitive detail database error.",
            response.text,
        )
        mock_load_agent_template.assert_called_once_with(
            self.agent_template_id,
            self.database_file,
        )

    def test_administrator_sees_allowed_draft_transitions(
        self,
    ):
        self.sign_in_as_admin()

        response = self.client.get(
            f"/agent-templates/"
            f"{self.agent_template_id}/edit"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Edit agent template",
            response.text,
        )
        self.assertIn('name="csrf_token"', response.text)
        self.assertIn(
            'name="expected_status"',
            response.text,
        )
        self.assertIn('value="draft"', response.text)
        self.assertIn('value="active"', response.text)
        self.assertNotIn(
            'value="inactive"',
            response.text,
        )
        self.assertIn(
            self.original_system_prompt,
            unescape(response.text),
        )

    @patch("web_app.update_agent_template")
    @patch("web_app.log_activity")
    def test_viewer_cannot_open_or_submit_edit_form(
        self,
        mock_log_activity,
        mock_update_agent_template,
    ):
        self.sign_in_as_viewer()
        mock_log_activity.reset_mock()

        get_response = self.client.get(
            f"/agent-templates/"
            f"{self.agent_template_id}/edit"
        )
        post_response = self.client.post(
            f"/agent-templates/"
            f"{self.agent_template_id}/edit",
            data={
                "csrf_token": "forged-token",
                "expected_status": "draft",
                "name": "Unauthorized Update",
                "description": "Must not be saved.",
                "system_prompt": "Unauthorized instructions.",
                "model_name": "gpt-6-astra",
                "status": "active",
            },
        )

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(get_response.text, "Access denied.")
        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(post_response.text, "Access denied.")
        mock_update_agent_template.assert_not_called()
        self.assertEqual(mock_log_activity.call_count, 2)
        mock_log_activity.assert_called_with(
            "Web agent-template edit access denied "
            f"for user {self.viewer_username}."
        )

    @patch("web_app.log_activity")
    def test_administrator_updates_and_activates_template(
        self,
        mock_log_activity,
    ):
        self.sign_in_as_admin()
        csrf_token = self.get_edit_csrf_token()
        mock_log_activity.reset_mock()

        response = self.client.post(
            f"/agent-templates/"
            f"{self.agent_template_id}/edit",
            data={
                "csrf_token": csrf_token,
                "expected_status": "draft",
                "name": "Updated Browser Agent",
                "description": (
                    "Updated through the Day 146 form."
                ),
                "system_prompt": (
                    "Use the updated protected instructions."
                ),
                "model_name": "gpt-6-astra",
                "status": "active",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            (
                "http://testserver/agent-templates/"
                f"{self.agent_template_id}"
            ),
        )

        stored_template = load_agent_template_by_id(
            self.agent_template_id,
            self.database_file,
        )
        self.assertIsNotNone(stored_template)

        if stored_template is None:
            self.fail(
                "The browser-updated template was not found."
            )

        self.assertEqual(
            stored_template["name"],
            "Updated Browser Agent",
        )
        self.assertEqual(
            stored_template["description"],
            "Updated through the Day 146 form.",
        )
        self.assertEqual(
            stored_template["system_prompt"],
            "Use the updated protected instructions.",
        )
        self.assertEqual(
            stored_template["model_name"],
            "gpt-6-astra",
        )
        self.assertEqual(
            stored_template["status"],
            "active",
        )

        mock_log_activity.assert_called_once_with(
            f"Web agent template {self.agent_template_id} "
            f"was updated to active by user "
            f"{self.admin_username}."
        )

    @patch("web_app.update_agent_template")
    @patch("web_app.log_activity")
    def test_edit_rejects_invalid_csrf_token(
        self,
        mock_log_activity,
        mock_update_agent_template,
    ):
        self.sign_in_as_admin()
        mock_log_activity.reset_mock()

        response = self.client.post(
            f"/agent-templates/"
            f"{self.agent_template_id}/edit",
            data={
                "csrf_token": "invalid-csrf-token",
                "expected_status": "draft",
                "name": "CSRF Update",
                "description": "Must not be saved.",
                "system_prompt": "Protected instructions.",
                "model_name": "gpt-6-astra",
                "status": "active",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.text,
            "Your form could not be verified.",
        )
        mock_update_agent_template.assert_not_called()
        mock_log_activity.assert_called_once_with(
            "Web agent-template edit CSRF validation "
            f"failed for user {self.admin_username}."
        )

        stored_template = load_agent_template_by_id(
            self.agent_template_id,
            self.database_file,
        )
        self.assertEqual(
            stored_template["name"],
            self.original_name,
        )
        self.assertEqual(
            stored_template["status"],
            "draft",
        )

    def test_active_template_cannot_return_to_draft(
        self,
    ):
        activated = update_agent_template(
            self.administrator,
            self.agent_template_id,
            self.original_name,
            self.original_description,
            self.original_system_prompt,
            self.original_model_name,
            "active",
            "draft",
            self.database_file,
        )
        self.assertTrue(activated)

        self.sign_in_as_admin()
        csrf_token = self.get_edit_csrf_token()

        response = self.client.post(
            f"/agent-templates/"
            f"{self.agent_template_id}/edit",
            data={
                "csrf_token": csrf_token,
                "expected_status": "active",
                "name": "Forbidden Draft Update",
                "description": self.original_description,
                "system_prompt": self.original_system_prompt,
                "model_name": self.original_model_name,
                "status": "draft",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Agent template could not be updated.",
            response.text,
        )
        self.assertIn(
            "Forbidden Draft Update",
            response.text,
        )

        stored_template = load_agent_template_by_id(
            self.agent_template_id,
            self.database_file,
        )
        self.assertEqual(
            stored_template["name"],
            self.original_name,
        )
        self.assertEqual(
            stored_template["status"],
            "active",
        )

    def test_stale_edit_form_does_not_replace_newer_update(
        self,
    ):
        self.sign_in_as_admin()
        csrf_token = self.get_edit_csrf_token()

        updated_elsewhere = update_agent_template(
            self.administrator,
            self.agent_template_id,
            "Updated by Another Request",
            self.original_description,
            self.original_system_prompt,
            self.original_model_name,
            "active",
            "draft",
            self.database_file,
        )
        self.assertTrue(updated_elsewhere)

        response = self.client.post(
            f"/agent-templates/"
            f"{self.agent_template_id}/edit",
            data={
                "csrf_token": csrf_token,
                "expected_status": "draft",
                "name": "Stale Browser Update",
                "description": self.original_description,
                "system_prompt": self.original_system_prompt,
                "model_name": self.original_model_name,
                "status": "active",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "refresh the page",
            response.text,
        )
        self.assertIn(
            "Stale Browser Update",
            response.text,
        )

        stored_template = load_agent_template_by_id(
            self.agent_template_id,
            self.database_file,
        )
        self.assertEqual(
            stored_template["name"],
            "Updated by Another Request",
        )
        self.assertEqual(
            stored_template["status"],
            "active",
        )

    @patch(
        "web_app.update_agent_template",
        side_effect=sqlite3.Error(
            "Sensitive edit database error."
        ),
    )
    def test_edit_database_error_is_safe_and_preserves_values(
        self,
        mock_update_agent_template,
    ):
        self.sign_in_as_admin()
        csrf_token = self.get_edit_csrf_token()

        response = self.client.post(
            f"/agent-templates/"
            f"{self.agent_template_id}/edit",
            data={
                "csrf_token": csrf_token,
                "expected_status": "draft",
                "name": "Preserved Database Error Name",
                "description": (
                    "Preserved database error description."
                ),
                "system_prompt": (
                    "Preserved database error instructions."
                ),
                "model_name": "preserved-model",
                "status": "active",
            },
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "The agent template could not be saved "
            "because the database is unavailable.",
            response.text,
        )
        self.assertNotIn(
            "Sensitive edit database error.",
            response.text,
        )
        self.assertIn(
            "Preserved Database Error Name",
            response.text,
        )
        self.assertIn(
            "Preserved database error description.",
            response.text,
        )
        self.assertIn(
            "Preserved database error instructions.",
            response.text,
        )
        self.assertIn(
            "preserved-model",
            response.text,
        )
        mock_update_agent_template.assert_called_once()


if __name__ == "__main__":
    unittest.main()