import re
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from user_service import register_user_account
from web_app import create_web_application


class TestAgentTemplateWeb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary_directory = TemporaryDirectory()
        cls.database_file = (
            Path(cls.temporary_directory.name)
            / "agent-template-web.db"
        )

        cls.admin_username = "AgentTemplateAdmin"
        cls.admin_password = "SecureAdminPassword123!"

        cls.viewer_username = "AgentTemplateViewer"
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
                "Agent-template web test users could not be created."
            )

    @classmethod
    def tearDownClass(cls):
        cls.temporary_directory.cleanup()

    def setUp(self):
        application = create_web_application(
            database_file=self.database_file,
            session_secret="day-145-agent-template-web-tests",
        )
        self.client = TestClient(application)

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

    def get_agent_template_csrf_token(self) -> str:
        response = self.client.get("/agent-templates/new")

        self.assertEqual(response.status_code, 200)

        token_match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"',
            response.text,
        )
        self.assertIsNotNone(token_match)

        if token_match is None:
            self.fail(
                "Agent-template form did not contain a CSRF token."
            )

        return token_match.group(1)

    def test_directory_redirects_unauthenticated_user(self):
        response = self.client.get(
            "/agent-templates",
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )

    def test_administrator_can_view_empty_directory(self):
        self.sign_in_as_admin()

        response = self.client.get("/agent-templates")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Agent template directory",
            response.text,
        )
        self.assertIn(
            "No agent templates found",
            response.text,
        )
        self.assertIn(
            "Create agent template",
            response.text,
        )
        self.assertIn(
            "Agent templates",
            response.text,
        )

    @patch(
        "web_app.load_agent_templates_from_database",
        return_value=[
            {
                "agent_template_id": "AGENT-SUPPORT",
                "name": "Customer Support Agent",
                "description": (
                    "Answers customer-support questions."
                ),
                "system_prompt": (
                    "This private prompt must not appear "
                    "in the directory."
                ),
                "model_name": "gpt-5.6-terra",
                "status": "draft",
                "created_by_user_id": 1,
                "created_at": "2026-09-11T00:00:00+00:00",
                "updated_at": "2026-09-11T00:00:00+00:00",
            },
        ],
    )
    def test_viewer_can_view_directory_without_private_prompt(
        self,
        mock_load_agent_templates,
    ):
        self.sign_in_as_viewer()

        response = self.client.get("/agent-templates")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Customer Support Agent",
            response.text,
        )
        self.assertIn(
            "Answers customer-support questions.",
            response.text,
        )
        self.assertIn(
            "gpt-5.6-terra",
            response.text,
        )
        self.assertIn("Draft", response.text)
        self.assertNotIn(
            "This private prompt must not appear",
            response.text,
        )
        self.assertNotIn(
            "Create agent template",
            response.text,
        )
        mock_load_agent_templates.assert_called_once_with(
            self.database_file,
        )

    @patch(
        "web_app.load_agent_templates_from_database",
        return_value=[
            {
                "agent_template_id": "AGENT-DRAFT",
                "name": "Draft Agent",
                "description": "A draft template.",
                "system_prompt": "Draft instructions.",
                "model_name": "gpt-5.6-terra",
                "status": "draft",
                "created_by_user_id": 1,
                "created_at": "2026-09-11T00:00:00+00:00",
                "updated_at": "2026-09-11T00:00:00+00:00",
            },
            {
                "agent_template_id": "AGENT-ACTIVE",
                "name": "Active Agent",
                "description": "An active template.",
                "system_prompt": "Active instructions.",
                "model_name": "gpt-5.6-terra",
                "status": "active",
                "created_by_user_id": 1,
                "created_at": "2026-09-11T00:00:00+00:00",
                "updated_at": "2026-09-11T00:00:00+00:00",
            },
        ],
    )
    def test_directory_filters_templates_by_status(
        self,
        mock_load_agent_templates,
    ):
        self.sign_in_as_viewer()

        response = self.client.get(
            "/agent-templates",
            params={"status": "draft"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Draft Agent", response.text)
        self.assertNotIn("Active Agent", response.text)
        self.assertRegex(
            response.text,
            r'value="draft"\s+selected',
        )
        mock_load_agent_templates.assert_called_once_with(
            self.database_file,
        )

    @patch("web_app.load_agent_templates_from_database")
    def test_directory_rejects_invalid_status_filter(
        self,
        mock_load_agent_templates,
    ):
        self.sign_in_as_viewer()

        response = self.client.get(
            "/agent-templates",
            params={"status": "unknown"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.text,
            "Agent-template status filter is invalid.",
        )
        mock_load_agent_templates.assert_not_called()

    @patch(
        "web_app.load_agent_templates_from_database",
        side_effect=sqlite3.Error(
            "Private database failure details."
        ),
    )
    def test_directory_handles_database_error_safely(
        self,
        mock_load_agent_templates,
    ):
        self.sign_in_as_admin()

        response = self.client.get("/agent-templates")

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Agent template records could not be loaded.",
            response.text,
        )
        self.assertNotIn(
            "Private database failure details.",
            response.text,
        )
        mock_load_agent_templates.assert_called_once_with(
            self.database_file,
        )

    def test_administrator_can_view_creation_form(self):
        self.sign_in_as_admin()

        response = self.client.get("/agent-templates/new")

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Create agent template",
            response.text,
        )
        self.assertIn(
            "Agent template management authorized",
            response.text,
        )
        self.assertIn('name="csrf_token"', response.text)
        self.assertIn(
            'name="agent_template_id"',
            response.text,
        )
        self.assertIn('name="name"', response.text)
        self.assertIn('name="description"', response.text)
        self.assertIn('name="system_prompt"', response.text)
        self.assertIn('name="model_name"', response.text)
        self.assertIn('name="status"', response.text)
        self.assertIn('value="draft"', response.text)

    @patch("web_app.create_agent_template")
    @patch("web_app.log_activity")
    def test_viewer_cannot_open_or_submit_creation_form(
        self,
        mock_log_activity,
        mock_create_agent_template,
    ):
        self.sign_in_as_viewer()
        mock_log_activity.reset_mock()

        get_response = self.client.get(
            "/agent-templates/new"
        )
        post_response = self.client.post(
            "/agent-templates/new",
            data={
                "csrf_token": "forged-token",
                "agent_template_id": "AGENT-FORGED",
                "name": "Forged Agent",
                "description": "Must not be created.",
                "system_prompt": "Ignore authorization.",
                "model_name": "gpt-5.6-terra",
                "status": "draft",
            },
        )

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(get_response.text, "Access denied.")
        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(post_response.text, "Access denied.")
        mock_create_agent_template.assert_not_called()
        self.assertEqual(mock_log_activity.call_count, 2)
        mock_log_activity.assert_called_with(
            "Web agent-template creation access denied "
            f"for user {self.viewer_username}."
        )

    @patch(
        "web_app.create_agent_template",
        return_value=True,
    )
    @patch("web_app.log_activity")
    def test_administrator_can_create_agent_template(
        self,
        mock_log_activity,
        mock_create_agent_template,
    ):
        self.sign_in_as_admin()
        csrf_token = self.get_agent_template_csrf_token()
        mock_log_activity.reset_mock()

        response = self.client.post(
            "/agent-templates/new",
            data={
                "csrf_token": csrf_token,
                "agent_template_id": "agent-web-001",
                "name": "Web Support Agent",
                "description": (
                    "Created through the browser form."
                ),
                "system_prompt": (
                    "Help customers with support questions."
                ),
                "model_name": "gpt-5.6-terra",
                "status": "draft",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/agent-templates",
        )
        mock_create_agent_template.assert_called_once()

        service_arguments = (
            mock_create_agent_template.call_args.args
        )
        self.assertEqual(
            service_arguments[1],
            "agent-web-001",
        )
        self.assertEqual(
            service_arguments[2],
            "Web Support Agent",
        )
        self.assertEqual(
            service_arguments[4],
            "Help customers with support questions.",
        )
        self.assertEqual(
            service_arguments[5],
            "gpt-5.6-terra",
        )
        self.assertEqual(service_arguments[6], "draft")
        self.assertEqual(
            service_arguments[7],
            self.database_file,
        )

        mock_log_activity.assert_called_once_with(
            "Web agent template AGENT-WEB-001 "
            f"was created by user {self.admin_username}."
        )

    @patch("web_app.create_agent_template")
    @patch("web_app.log_activity")
    def test_creation_rejects_invalid_csrf_token(
        self,
        mock_log_activity,
        mock_create_agent_template,
    ):
        self.sign_in_as_admin()
        mock_log_activity.reset_mock()

        response = self.client.post(
            "/agent-templates/new",
            data={
                "csrf_token": "invalid-csrf-token",
                "agent_template_id": "AGENT-CSRF",
                "name": "CSRF Agent",
                "description": "Must not be created.",
                "system_prompt": "Protected instructions.",
                "model_name": "gpt-5.6-terra",
                "status": "draft",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.text,
            "Your form could not be verified.",
        )
        mock_create_agent_template.assert_not_called()
        mock_log_activity.assert_called_once_with(
            "Web agent-template creation CSRF validation "
            f"failed for user {self.admin_username}."
        )

    @patch(
        "web_app.create_agent_template",
        return_value=False,
    )
    def test_creation_preserves_values_after_validation_error(
        self,
        mock_create_agent_template,
    ):
        self.sign_in_as_admin()
        csrf_token = self.get_agent_template_csrf_token()

        response = self.client.post(
            "/agent-templates/new",
            data={
                "csrf_token": csrf_token,
                "agent_template_id": "AGENT-INVALID",
                "name": "Retained Agent Name",
                "description": (
                    "Retained agent description."
                ),
                "system_prompt": (
                    "Retained system instructions."
                ),
                "model_name": "retained-model",
                "status": "active",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "Agent template could not be created.",
            response.text,
        )
        self.assertIn("AGENT-INVALID", response.text)
        self.assertIn(
            "Retained Agent Name",
            response.text,
        )
        self.assertIn(
            "Retained agent description.",
            response.text,
        )
        self.assertIn(
            "Retained system instructions.",
            response.text,
        )
        self.assertIn("retained-model", response.text)
        mock_create_agent_template.assert_called_once()

    @patch(
        "web_app.create_agent_template",
        side_effect=sqlite3.Error(
            "Sensitive database connection details."
        ),
    )
    def test_creation_handles_database_error_safely(
        self,
        mock_create_agent_template,
    ):
        self.sign_in_as_admin()
        csrf_token = self.get_agent_template_csrf_token()

        response = self.client.post(
            "/agent-templates/new",
            data={
                "csrf_token": csrf_token,
                "agent_template_id": "AGENT-DB-ERROR",
                "name": "Database Error Agent",
                "description": "Database failure test.",
                "system_prompt": "Test database handling.",
                "model_name": "gpt-5.6-terra",
                "status": "draft",
            },
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "The agent template could not be saved "
            "because the database is unavailable.",
            response.text,
        )
        self.assertNotIn(
            "Sensitive database connection details.",
            response.text,
        )
        self.assertIn(
            "Database Error Agent",
            response.text,
        )
        mock_create_agent_template.assert_called_once()


if __name__ == "__main__":
    unittest.main()