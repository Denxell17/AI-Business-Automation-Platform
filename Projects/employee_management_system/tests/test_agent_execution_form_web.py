import re
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from agent_execution_service import (
    MAX_AGENT_EXECUTION_INPUT_LENGTH,
    SAFE_AGENT_PROVIDER_ERROR_MESSAGE,
)
from agent_provider import AgentProviderError
from database import (
    insert_agent_template,
    load_agent_executions_for_template,
    load_user_account_by_username,
)
from user_service import register_user_account
from web_app import create_web_application


class DeterministicAgentProvider:
    def __init__(
        self,
        output="Deterministic browser response.",
        error=None,
    ):
        self.output = output
        self.error = error
        self.calls = []

    def generate_response(
        self,
        *,
        model_name,
        system_prompt,
        input_text,
    ):
        self.calls.append(
            {
                "model_name": model_name,
                "system_prompt": system_prompt,
                "input_text": input_text,
            }
        )

        if self.error is not None:
            raise self.error

        return self.output


class DeterministicProviderFactory:
    def __init__(self, provider):
        self.provider = provider
        self.error = None
        self.call_count = 0

    def __call__(self):
        self.call_count += 1

        if self.error is not None:
            raise self.error

        return self.provider


class TestAgentExecutionFormWeb(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name)
            / "agent-execution-form-web.db"
        )

        self.admin_username = "AgentExecutionFormAdmin"
        self.admin_password = "SecureAdminPassword123!"
        self.viewer_username = "AgentExecutionFormViewer"
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
                "The Agent Execution form administrator "
                "was not found."
            )

        self.agent_template_id = "AGENT-WEB-RUN"
        self.system_prompt = (
            "Protect customer information and respond clearly."
        )
        self.model_name = "test-browser-model"

        self.create_template(
            self.agent_template_id,
            "Browser Execution Agent",
            "active",
        )

        self.provider = DeterministicAgentProvider()
        self.provider_factory = DeterministicProviderFactory(
            self.provider
        )

        application = create_web_application(
            database_file=self.database_file,
            session_secret="day-150-agent-execution-form-tests",
            agent_provider_factory=self.provider_factory,
        )
        self.client = TestClient(application)

    def tearDown(self):
        self.client.close()
        self.temporary_directory.cleanup()

    def create_template(
        self,
        agent_template_id,
        name,
        status,
    ):
        inserted = insert_agent_template(
            {
                "agent_template_id": agent_template_id,
                "name": name,
                "description": (
                    "Used by Agent Execution form tests."
                ),
                "system_prompt": self.system_prompt,
                "model_name": self.model_name,
                "status": status,
                "created_by_user_id": self.administrator[
                    "user_id"
                ],
                "created_at": "2026-09-11T05:00:00+00:00",
                "updated_at": "2026-09-11T05:00:00+00:00",
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

    def template_url(self, template_id=None):
        selected_template_id = (
            template_id
            if template_id is not None
            else self.agent_template_id
        )
        return f"/agent-templates/{selected_template_id}"

    def execution_submit_url(self, template_id=None):
        return (
            f"{self.template_url(template_id)}"
            "/executions"
        )

    def get_execution_csrf_token(self):
        response = self.client.get(self.template_url())
        self.assertEqual(response.status_code, 200)

        match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"',
            response.text,
        )
        self.assertIsNotNone(match)

        if match is None:
            self.fail(
                "The Agent Execution CSRF token was not rendered."
            )

        return match.group(1)

    def test_active_template_detail_displays_execution_form(self):
        self.sign_in_as_admin()

        response = self.client.get(self.template_url())

        self.assertEqual(response.status_code, 200)
        self.assertIn("Run Agent Template", response.text)
        self.assertIn('name="csrf_token"', response.text)
        self.assertIn('name="input_text"', response.text)
        self.assertIn('maxlength="10000"', response.text)
        self.assertIn(
            (
                'action="http://testserver'
                f'{self.execution_submit_url()}"'
            ),
            response.text,
        )

    def test_inactive_template_does_not_display_execution_form(self):
        inactive_template_id = "AGENT-WEB-INACTIVE"
        self.create_template(
            inactive_template_id,
            "Inactive Browser Agent",
            "inactive",
        )
        self.sign_in_as_admin()

        response = self.client.get(
            self.template_url(inactive_template_id)
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('name="input_text"', response.text)
        self.assertNotIn("Run Agent Template", response.text)

    def test_inactive_template_submission_is_rejected(self):
        inactive_template_id = "AGENT-WEB-INACTIVE-SUBMIT"
        self.create_template(
            inactive_template_id,
            "Inactive Submission Agent",
            "inactive",
        )
        self.sign_in_as_admin()
        csrf_token = self.get_execution_csrf_token()

        response = self.client.post(
            self.execution_submit_url(inactive_template_id),
            data={
                "csrf_token": csrf_token,
                "input_text": "Attempt inactive execution.",
            },
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.text,
            "Only an Active Agent Template can be executed.",
        )
        self.assertEqual(self.provider_factory.call_count, 0)
        self.assertEqual(self.provider.calls, [])

    def test_missing_template_submission_returns_not_found(self):
        self.sign_in_as_admin()
        csrf_token = self.get_execution_csrf_token()

        response = self.client.post(
            self.execution_submit_url("AGENT-WEB-MISSING"),
            data={
                "csrf_token": csrf_token,
                "input_text": "Attempt missing execution.",
            },
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.text,
            "The requested Agent Template was not found.",
        )
        self.assertEqual(self.provider_factory.call_count, 0)
        self.assertEqual(self.provider.calls, [])

    def test_unauthenticated_submission_redirects_to_login(self):
        response = self.client.post(
            self.execution_submit_url(),
            data={
                "csrf_token": "untrusted-token",
                "input_text": "Private business input.",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(
            response.headers["location"],
            "http://testserver/login",
        )
        self.assertEqual(self.provider_factory.call_count, 0)
        self.assertEqual(self.provider.calls, [])

    @patch("web_app.log_activity")
    def test_viewer_cannot_submit_execution(
        self,
        mock_log_activity,
    ):
        self.sign_in_as_viewer()
        mock_log_activity.reset_mock()

        response = self.client.post(
            self.execution_submit_url(),
            data={
                "csrf_token": "untrusted-token",
                "input_text": "Private business input.",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.text, "Access denied.")
        self.assertEqual(self.provider_factory.call_count, 0)
        self.assertEqual(self.provider.calls, [])
        mock_log_activity.assert_called_once()

    @patch("web_app.log_activity")
    def test_invalid_csrf_token_is_rejected_before_provider_call(
        self,
        mock_log_activity,
    ):
        self.sign_in_as_admin()
        mock_log_activity.reset_mock()

        response = self.client.post(
            self.execution_submit_url(),
            data={
                "csrf_token": "forged-token",
                "input_text": "Private business input.",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.text,
            "Your form could not be verified.",
        )
        self.assertEqual(self.provider_factory.call_count, 0)
        self.assertEqual(self.provider.calls, [])
        mock_log_activity.assert_called_once()

    def test_invalid_input_is_rejected_before_provider_creation(self):
        self.sign_in_as_admin()
        csrf_token = self.get_execution_csrf_token()

        invalid_values = (
            "",
            "x" * (MAX_AGENT_EXECUTION_INPUT_LENGTH + 1),
        )

        for input_text in invalid_values:
            with self.subTest(input_length=len(input_text)):
                response = self.client.post(
                    self.execution_submit_url(),
                    data={
                        "csrf_token": csrf_token,
                        "input_text": input_text,
                    },
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn(
                    "Enter execution input between 1 and 10000 "
                    "characters.",
                    response.text,
                )

        self.assertEqual(self.provider_factory.call_count, 0)
        self.assertEqual(self.provider.calls, [])

    def test_provider_configuration_failure_is_safe(self):
        unsafe_detail = (
            "missing configuration with secret test-api-key"
        )
        self.provider_factory.error = ValueError(unsafe_detail)
        self.sign_in_as_admin()
        csrf_token = self.get_execution_csrf_token()

        response = self.client.post(
            self.execution_submit_url(),
            data={
                "csrf_token": csrf_token,
                "input_text": "Private business input.",
            },
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn(
            "The AI provider is not configured for execution.",
            response.text,
        )
        self.assertNotIn(unsafe_detail, response.text)
        self.assertIn(
            "Private business input.",
            response.text,
        )
        self.assertEqual(self.provider_factory.call_count, 1)
        self.assertEqual(self.provider.calls, [])
        self.assertEqual(
            load_agent_executions_for_template(
                self.agent_template_id,
                self.database_file,
            ),
            [],
        )

    def test_successful_execution_redirects_to_protected_detail(self):
        self.sign_in_as_admin()
        csrf_token = self.get_execution_csrf_token()

        response = self.client.post(
            self.execution_submit_url(),
            data={
                "csrf_token": csrf_token,
                "input_text": "  Summarize this customer request.  ",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)
        self.assertEqual(self.provider_factory.call_count, 1)
        self.assertEqual(
            self.provider.calls,
            [
                {
                    "model_name": self.model_name,
                    "system_prompt": self.system_prompt,
                    "input_text": (
                        "Summarize this customer request."
                    ),
                }
            ],
        )

        execution_list = load_agent_executions_for_template(
            self.agent_template_id,
            self.database_file,
        )
        self.assertEqual(len(execution_list), 1)

        agent_execution = execution_list[0]
        self.assertEqual(
            agent_execution["status"],
            "completed",
        )
        self.assertEqual(
            agent_execution["output_text"],
            "Deterministic browser response.",
        )
        self.assertEqual(
            response.headers["location"],
            (
                "http://testserver"
                f"{self.execution_submit_url()}/"
                f"{agent_execution['agent_execution_id']}"
            ),
        )

        detail_response = self.client.get(
            response.headers["location"]
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertIn(
            "Deterministic browser response.",
            detail_response.text,
        )

    def test_provider_failure_redirects_to_safe_failed_detail(self):
        unsafe_detail = (
            "provider failed with secret test-api-key"
        )
        self.provider.error = AgentProviderError(
            unsafe_detail
        )
        self.sign_in_as_admin()
        csrf_token = self.get_execution_csrf_token()

        response = self.client.post(
            self.execution_submit_url(),
            data={
                "csrf_token": csrf_token,
                "input_text": "Trigger a provider failure.",
            },
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 303)

        execution_list = load_agent_executions_for_template(
            self.agent_template_id,
            self.database_file,
        )
        self.assertEqual(len(execution_list), 1)

        agent_execution = execution_list[0]
        self.assertEqual(agent_execution["status"], "failed")
        self.assertEqual(
            agent_execution["error_message"],
            SAFE_AGENT_PROVIDER_ERROR_MESSAGE,
        )
        self.assertNotIn(
            unsafe_detail,
            agent_execution["error_message"],
        )

        detail_response = self.client.get(
            response.headers["location"]
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertIn(
            SAFE_AGENT_PROVIDER_ERROR_MESSAGE,
            detail_response.text,
        )
        self.assertNotIn(unsafe_detail, detail_response.text)

    @patch(
        "web_app.execute_agent_template",
        side_effect=sqlite3.OperationalError(
            "private database failure detail"
        ),
    )
    def test_database_failure_is_safe_and_preserves_input(
        self,
        mock_execute_agent_template,
    ):
        self.sign_in_as_admin()
        csrf_token = self.get_execution_csrf_token()
        hostile_input = "<script>private input</script>"

        response = self.client.post(
            self.execution_submit_url(),
            data={
                "csrf_token": csrf_token,
                "input_text": hostile_input,
            },
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "The Agent Execution could not be saved because "
            "the database is unavailable.",
            response.text,
        )
        self.assertIn(
            "&lt;script&gt;private input&lt;/script&gt;",
            response.text,
        )
        self.assertNotIn(hostile_input, response.text)
        self.assertNotIn(
            "private database failure detail",
            response.text,
        )
        mock_execute_agent_template.assert_called_once()


if __name__ == "__main__":
    unittest.main()