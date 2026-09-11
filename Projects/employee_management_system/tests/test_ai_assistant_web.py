import re
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from agent_provider import AgentProviderError
from ai_assistant_service import (
    AI_ASSISTANT_SYSTEM_PROMPT,
    MAX_AI_ASSISTANT_QUESTION_LENGTH,
    SAFE_AI_ASSISTANT_ERROR_MESSAGE,
)
from database import (
    load_user_account_by_username,
)
from user_service import register_user_account
from web_app import create_web_application


class DeterministicAssistantProvider:
    def __init__(
        self,
        output="Deterministic Assistant browser response.",
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


class DeterministicAssistantSettingsLoader:
    def __init__(
        self,
        model_name="test-assistant-model",
    ):
        self.model_name = model_name
        self.error = None
        self.call_count = 0

    def __call__(self):
        self.call_count += 1

        if self.error is not None:
            raise self.error

        return {
            "model_name": self.model_name,
        }


class TestAiAssistantWeb(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name)
            / "ai-assistant-web.db"
        )

        self.admin_username = "AssistantWebAdmin"
        self.admin_password = "SecureAdminPassword123!"
        self.viewer_username = "AssistantWebViewer"
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

        self.provider = DeterministicAssistantProvider()
        self.provider_factory = DeterministicProviderFactory(
            self.provider
        )
        self.settings_loader = (
            DeterministicAssistantSettingsLoader()
        )

        application = create_web_application(
            database_file=self.database_file,
            session_secret="day-152-ai-assistant-web-tests",
            agent_provider_factory=self.provider_factory,
            ai_assistant_settings_loader=(
                self.settings_loader
            ),
        )
        self.client = TestClient(application)

    def tearDown(self):
        self.client.close()
        self.temporary_directory.cleanup()

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

    def get_csrf_token(self):
        response = self.client.get("/ai-assistant")
        self.assertEqual(response.status_code, 200)

        match = re.search(
            r'name="csrf_token"\s+value="([^"]+)"',
            response.text,
        )
        self.assertIsNotNone(match)

        if match is None:
            self.fail(
                "The AI Assistant CSRF token was not rendered."
            )

        return match.group(1)

    def test_get_and_post_redirect_unauthenticated_user(self):
        get_response = self.client.get(
            "/ai-assistant",
            follow_redirects=False,
        )
        post_response = self.client.post(
            "/ai-assistant",
            data={
                "csrf_token": "untrusted-token",
                "question": "Private business question.",
            },
            follow_redirects=False,
        )

        for response in (get_response, post_response):
            with self.subTest(method=response.request.method):
                self.assertEqual(response.status_code, 303)
                self.assertEqual(
                    response.headers["location"],
                    "http://testserver/login",
                )

        self.assertEqual(self.settings_loader.call_count, 0)
        self.assertEqual(self.provider_factory.call_count, 0)
        self.assertEqual(self.provider.calls, [])

    @patch("web_app.log_activity")
    def test_viewer_cannot_access_ai_assistant(
        self,
        mock_log_activity,
    ):
        self.sign_in_as_viewer()
        mock_log_activity.reset_mock()

        home_response = self.client.get("/")
        get_response = self.client.get("/ai-assistant")
        post_response = self.client.post(
            "/ai-assistant",
            data={
                "csrf_token": "untrusted-token",
                "question": "Private business question.",
            },
        )

        self.assertEqual(home_response.status_code, 200)
        self.assertNotIn(
            'href="http://testserver/ai-assistant"',
            home_response.text,
        )
        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(get_response.text, "Access denied.")
        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(post_response.text, "Access denied.")
        self.assertEqual(mock_log_activity.call_count, 2)
        self.assertEqual(self.settings_loader.call_count, 0)
        self.assertEqual(self.provider_factory.call_count, 0)
        self.assertEqual(self.provider.calls, [])

        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(get_response.text, "Access denied.")
        self.assertEqual(post_response.status_code, 403)
        self.assertEqual(post_response.text, "Access denied.")
        self.assertEqual(mock_log_activity.call_count, 2)
        self.assertEqual(self.settings_loader.call_count, 0)
        self.assertEqual(self.provider_factory.call_count, 0)
        self.assertEqual(self.provider.calls, [])

    def test_administrator_views_form_without_provider_creation(self):
        self.sign_in_as_admin()

        response = self.client.get("/ai-assistant")

        self.assertEqual(response.status_code, 200)
        self.assertIn("<h1", response.text)
        self.assertIn("AI Assistant", response.text)
        self.assertIn('name="csrf_token"', response.text)
        self.assertIn('name="question"', response.text)
        self.assertIn('maxlength="10000"', response.text)
        self.assertIn(
            'class="navigation-link is-active"',
            response.text,
        )
        self.assertIn(
            'href="http://testserver/ai-assistant"',
            response.text,
        )
        self.assertIn('aria-current="page"', response.text)
        self.assertIn(
            'action="http://testserver/ai-assistant"',
            response.text,
        )
        self.assertIn(
            "This one-off interaction is not",
            response.text,
        )
        self.assertEqual(self.settings_loader.call_count, 0)
        self.assertEqual(self.provider_factory.call_count, 0)

    @patch("web_app.log_activity")
    def test_invalid_csrf_is_rejected_before_configuration(
        self,
        mock_log_activity,
    ):
        self.sign_in_as_admin()
        mock_log_activity.reset_mock()

        home_response = self.client.get("/")

        response = self.client.post(
            "/ai-assistant",
            data={
                "csrf_token": "forged-token",
                "question": "Private business question.",
            },
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.text,
            "Your form could not be verified.",
        )
        mock_log_activity.assert_called_once()
        self.assertEqual(self.settings_loader.call_count, 0)
        self.assertEqual(self.provider_factory.call_count, 0)

    def test_invalid_question_is_rejected_before_configuration(self):
        self.sign_in_as_admin()
        csrf_token = self.get_csrf_token()

        invalid_questions = (
            "",
            "x" * (MAX_AI_ASSISTANT_QUESTION_LENGTH + 1),
        )

        for question in invalid_questions:
            with self.subTest(question_length=len(question)):
                response = self.client.post(
                    "/ai-assistant",
                    data={
                        "csrf_token": csrf_token,
                        "question": question,
                    },
                )

                self.assertEqual(response.status_code, 400)
                self.assertIn(
                    "Enter a question between 1 and 10000 "
                    "characters.",
                    response.text,
                )

        self.assertEqual(self.settings_loader.call_count, 0)
        self.assertEqual(self.provider_factory.call_count, 0)

    def test_configuration_failure_is_safe_and_preserves_question(
        self,
    ):
        unsafe_detail = (
            "missing model with secret configuration detail"
        )
        self.settings_loader.error = ValueError(unsafe_detail)
        self.sign_in_as_admin()
        csrf_token = self.get_csrf_token()
        hostile_question = (
            "<script>private customer question</script>"
        )

        response = self.client.post(
            "/ai-assistant",
            data={
                "csrf_token": csrf_token,
                "question": hostile_question,
            },
        )

        self.assertEqual(response.status_code, 503)
        self.assertIn(
            "The AI Assistant is not configured.",
            response.text,
        )
        self.assertNotIn(unsafe_detail, response.text)
        self.assertIn(
            "&lt;script&gt;private customer "
            "question&lt;/script&gt;",
            response.text,
        )
        self.assertNotIn(hostile_question, response.text)
        self.assertEqual(self.settings_loader.call_count, 1)
        self.assertEqual(self.provider_factory.call_count, 0)

    def test_successful_question_displays_escaped_response(self):
        hostile_question = (
            "<script>summarize customer request</script>"
        )
        self.provider.output = (
            "<strong>Protected Assistant response.</strong>"
        )
        self.sign_in_as_admin()
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            "/ai-assistant",
            data={
                "csrf_token": csrf_token,
                "question": hostile_question,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "&lt;script&gt;summarize customer "
            "request&lt;/script&gt;",
            response.text,
        )
        self.assertNotIn(hostile_question, response.text)
        self.assertIn(
            "&lt;strong&gt;Protected Assistant "
            "response.&lt;/strong&gt;",
            response.text,
        )
        self.assertNotIn(self.provider.output, response.text)
        self.assertIn("test-assistant-model", response.text)
        self.assertEqual(self.settings_loader.call_count, 1)
        self.assertEqual(self.provider_factory.call_count, 1)
        self.assertEqual(
            self.provider.calls,
            [
                {
                    "model_name": "test-assistant-model",
                    "system_prompt": AI_ASSISTANT_SYSTEM_PROMPT,
                    "input_text": hostile_question,
                }
            ],
        )

    def test_provider_failure_displays_only_safe_error(self):
        unsafe_detail = (
            "provider failed with secret test-api-key"
        )
        self.provider.error = AgentProviderError(
            unsafe_detail
        )
        self.sign_in_as_admin()
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            "/ai-assistant",
            data={
                "csrf_token": csrf_token,
                "question": "Help with this workflow.",
            },
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn(
            SAFE_AI_ASSISTANT_ERROR_MESSAGE,
            response.text,
        )
        self.assertNotIn(unsafe_detail, response.text)
        self.assertEqual(self.settings_loader.call_count, 1)
        self.assertEqual(self.provider_factory.call_count, 1)

    @patch(
        "web_app.ask_ai_assistant",
        side_effect=sqlite3.OperationalError(
            "private database failure detail"
        ),
    )
    def test_database_failure_displays_only_safe_error(
        self,
        mock_ask_ai_assistant,
    ):
        self.sign_in_as_admin()
        csrf_token = self.get_csrf_token()

        response = self.client.post(
            "/ai-assistant",
            data={
                "csrf_token": csrf_token,
                "question": "Help with this workflow.",
            },
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn(
            "The AI Assistant could not verify your account.",
            response.text,
        )
        self.assertNotIn(
            "private database failure detail",
            response.text,
        )
        mock_ask_ai_assistant.assert_called_once()


if __name__ == "__main__":
    unittest.main()