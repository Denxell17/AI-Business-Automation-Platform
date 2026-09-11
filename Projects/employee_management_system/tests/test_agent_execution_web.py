import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from database import (
    insert_agent_execution,
    insert_agent_template,
    load_user_account_by_username,
)
from user_service import register_user_account
from web_app import create_web_application


class TestAgentExecutionWeb(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name)
            / "agent-execution-web.db"
        )

        self.admin_username = "AgentExecutionWebAdmin"
        self.admin_password = "SecureAdminPassword123!"
        self.viewer_username = "AgentExecutionWebViewer"
        self.viewer_password = "SecureViewerPassword123!"

        self.assertTrue(
            register_user_account(
                self.admin_username,
                self.admin_password,
                "admin",
                self.database_file,
            )
        )
        self.assertTrue(
            register_user_account(
                self.viewer_username,
                self.viewer_password,
                "viewer",
                self.database_file,
            )
        )

        self.administrator = load_user_account_by_username(
            self.admin_username,
            self.database_file,
        )
        self.assertIsNotNone(self.administrator)

        if self.administrator is None:
            self.fail(
                "The Agent Execution web administrator "
                "was not found."
            )

        self.agent_template_id = "AGENT-WEB-EXECUTION"
        self.completed_execution_id = (
            "AGENT-EXEC-WEB-COMPLETED"
        )
        self.failed_execution_id = (
            "AGENT-EXEC-WEB-FAILED"
        )
        self.completed_input = (
            "Private customer input. "
            "<script>alert('input')</script>"
        )
        self.completed_output = (
            "Protected generated output. "
            "<strong>Complete</strong>"
        )
        self.safe_error = (
            "The AI provider could not complete the request. "
            "<internal>"
        )

        self.create_template(
            self.agent_template_id,
            "Agent Execution Browser Test",
        )

        self.assertTrue(
            insert_agent_execution(
                {
                    "agent_execution_id": (
                        self.completed_execution_id
                    ),
                    "agent_template_id": (
                        self.agent_template_id
                    ),
                    "agent_template_name": (
                        "Agent Execution Browser Test"
                    ),
                    "model_name": "test-completed-model",
                    "status": "completed",
                    "input_text": self.completed_input,
                    "output_text": self.completed_output,
                    "error_message": None,
                    "requested_by_user_id": (
                        self.administrator["user_id"]
                    ),
                    "started_at": (
                        "2026-09-11T03:00:00+00:00"
                    ),
                    "finished_at": (
                        "2026-09-11T03:01:00+00:00"
                    ),
                },
                self.database_file,
            )
        )

        self.assertTrue(
            insert_agent_execution(
                {
                    "agent_execution_id": (
                        self.failed_execution_id
                    ),
                    "agent_template_id": (
                        self.agent_template_id
                    ),
                    "agent_template_name": (
                        "Agent Execution Browser Test"
                    ),
                    "model_name": "test-failed-model",
                    "status": "failed",
                    "input_text": (
                        "Request that produced a safe failure."
                    ),
                    "output_text": None,
                    "error_message": self.safe_error,
                    "requested_by_user_id": (
                        self.administrator["user_id"]
                    ),
                    "started_at": (
                        "2026-09-11T04:00:00+00:00"
                    ),
                    "finished_at": (
                        "2026-09-11T04:01:00+00:00"
                    ),
                },
                self.database_file,
            )
        )

        application = create_web_application(
            database_file=self.database_file,
            session_secret=(
                "day-148-agent-execution-web-tests"
            ),
        )
        self.client = TestClient(application)

    def tearDown(self):
        self.client.close()
        self.temporary_directory.cleanup()

    def create_template(
        self,
        agent_template_id,
        name,
    ):
        inserted = insert_agent_template(
            {
                "agent_template_id": agent_template_id,
                "name": name,
                "description": (
                    "Used by Agent Execution browser tests."
                ),
                "system_prompt": (
                    "Protect customer information."
                ),
                "model_name": "test-template-model",
                "status": "active",
                "created_by_user_id": self.administrator[
                    "user_id"
                ],
                "created_at": (
                    "2026-09-11T02:00:00+00:00"
                ),
                "updated_at": (
                    "2026-09-11T02:00:00+00:00"
                ),
            },
            self.database_file,
        )
        self.assertTrue(inserted)

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

    def history_url(self):
        return (
            f"/agent-templates/{self.agent_template_id}"
            "/executions"
        )

    def execution_url(self, agent_execution_id):
        return (
            f"/agent-templates/{self.agent_template_id}"
            f"/executions/{agent_execution_id}"
        )

    def test_history_and_detail_redirect_unauthenticated_user(
        self,
    ):
        urls = (
            self.history_url(),
            self.execution_url(
                self.completed_execution_id
            ),
        )

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(
                    url,
                    follow_redirects=False,
                )

                self.assertEqual(
                    response.status_code,
                    303,
                )
                self.assertEqual(
                    response.headers["location"],
                    "http://testserver/login",
                )

    @patch("web_app.log_activity")
    def test_viewer_cannot_view_execution_records(
        self,
        mock_log_activity,
    ):
        self.sign_in_as_viewer()
        mock_log_activity.reset_mock()

        history_response = self.client.get(
            self.history_url()
        )
        detail_response = self.client.get(
            self.execution_url(
                self.completed_execution_id
            )
        )

        self.assertEqual(
            history_response.status_code,
            403,
        )
        self.assertEqual(
            history_response.text,
            "Access denied.",
        )
        self.assertEqual(
            detail_response.status_code,
            403,
        )
        self.assertEqual(
            detail_response.text,
            "Access denied.",
        )
        self.assertEqual(mock_log_activity.call_count, 2)

    def test_administrator_views_newest_first_history(
        self,
    ):
        self.sign_in_as_admin()

        response = self.client.get(
            self.history_url()
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Agent Execution Browser Test executions",
            response.text,
        )
        self.assertIn(
            self.completed_execution_id,
            response.text,
        )
        self.assertIn(
            self.failed_execution_id,
            response.text,
        )
        self.assertIn(
            "test-completed-model",
            response.text,
        )
        self.assertIn(
            "test-failed-model",
            response.text,
        )
        self.assertLess(
            response.text.index(
                self.failed_execution_id
            ),
            response.text.index(
                self.completed_execution_id
            ),
        )

        self.assertNotIn(
            "Private customer input",
            response.text,
        )
        self.assertNotIn(
            "Protected generated output",
            response.text,
        )
        self.assertNotIn(
            "The AI provider could not complete",
            response.text,
        )

    def test_empty_execution_history_is_accessible(
        self,
    ):
        empty_template_id = "AGENT-WEB-EMPTY"
        self.create_template(
            empty_template_id,
            "Empty Execution Agent",
        )
        self.sign_in_as_admin()

        response = self.client.get(
            (
                f"/agent-templates/{empty_template_id}"
                "/executions"
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "No Agent Executions yet",
            response.text,
        )
        self.assertIn(
            "This Agent Template has no stored "
            "execution history.",
            response.text,
        )

    def test_completed_execution_detail_is_escaped(
        self,
    ):
        self.sign_in_as_admin()

        response = self.client.get(
            self.execution_url(
                self.completed_execution_id
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            self.completed_execution_id,
            response.text,
        )
        self.assertIn(
            "Private customer input.",
            response.text,
        )
        self.assertIn(
            "&lt;script&gt;",
            response.text,
        )
        self.assertNotIn(
            "<script>alert",
            response.text,
        )
        self.assertIn(
            "Protected generated output.",
            response.text,
        )
        self.assertIn(
            "&lt;strong&gt;Complete&lt;/strong&gt;",
            response.text,
        )
        self.assertNotIn(
            "<strong>Complete</strong>",
            response.text,
        )

    def test_failed_execution_detail_displays_safe_error(
        self,
    ):
        self.sign_in_as_admin()

        response = self.client.get(
            self.execution_url(
                self.failed_execution_id
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "Failed",
            response.text,
        )
        self.assertIn(
            "The AI provider could not complete "
            "the request.",
            response.text,
        )
        self.assertIn(
            "&lt;internal&gt;",
            response.text,
        )
        self.assertNotIn(
            "<internal>",
            response.text,
        )

    def test_missing_and_wrong_template_execution_return_not_found(
        self,
    ):
        other_template_id = "AGENT-WEB-OTHER"
        self.create_template(
            other_template_id,
            "Other Execution Agent",
        )
        self.sign_in_as_admin()

        missing_response = self.client.get(
            self.execution_url(
                "AGENT-EXEC-MISSING"
            )
        )
        wrong_template_response = self.client.get(
            (
                f"/agent-templates/{other_template_id}"
                f"/executions/{self.completed_execution_id}"
            )
        )

        self.assertEqual(
            missing_response.status_code,
            404,
        )
        self.assertIn(
            "The requested Agent Execution "
            "was not found.",
            missing_response.text,
        )
        self.assertEqual(
            wrong_template_response.status_code,
            404,
        )
        self.assertIn(
            "The requested Agent Execution "
            "was not found.",
            wrong_template_response.text,
        )

    @patch(
        "web_app.load_agent_executions_for_template",
        side_effect=sqlite3.Error(
            "Sensitive history database error."
        ),
    )
    def test_history_database_error_is_safe(
        self,
        mock_load_history,
    ):
        self.sign_in_as_admin()

        response = self.client.get(
            self.history_url()
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "Agent Execution history could not "
            "be loaded.",
            response.text,
        )
        self.assertNotIn(
            "Sensitive history database error.",
            response.text,
        )
        mock_load_history.assert_called_once_with(
            self.agent_template_id,
            self.database_file,
        )

    @patch(
        "web_app.load_agent_execution_by_id",
        side_effect=sqlite3.Error(
            "Sensitive detail database error."
        ),
    )
    def test_detail_database_error_is_safe(
        self,
        mock_load_execution,
    ):
        self.sign_in_as_admin()

        response = self.client.get(
            self.execution_url(
                self.completed_execution_id
            )
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "The Agent Execution could not be loaded.",
            response.text,
        )
        self.assertNotIn(
            "Sensitive detail database error.",
            response.text,
        )
        mock_load_execution.assert_called_once_with(
            self.completed_execution_id,
            self.database_file,
        )

    def test_template_detail_history_link_is_admin_only(
        self,
    ):
        self.sign_in_as_admin()

        administrator_response = self.client.get(
            f"/agent-templates/{self.agent_template_id}"
        )

        self.assertEqual(
            administrator_response.status_code,
            200,
        )
        self.assertIn(
            "View execution history",
            administrator_response.text,
        )

        self.sign_in_as_viewer()

        viewer_response = self.client.get(
            f"/agent-templates/{self.agent_template_id}"
        )

        self.assertEqual(viewer_response.status_code, 200)
        self.assertNotIn(
            "View execution history",
            viewer_response.text,
        )


if __name__ == "__main__":
    unittest.main()