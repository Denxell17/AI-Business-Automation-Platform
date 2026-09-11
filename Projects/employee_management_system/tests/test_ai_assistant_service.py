import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_provider import AgentProviderError
from ai_assistant_service import (
    AI_ASSISTANT_SYSTEM_PROMPT,
    MAX_AI_ASSISTANT_MODEL_NAME_LENGTH,
    MAX_AI_ASSISTANT_QUESTION_LENGTH,
    MAX_AI_ASSISTANT_RESPONSE_LENGTH,
    SAFE_AI_ASSISTANT_ERROR_MESSAGE,
    ask_ai_assistant,
)
from database import (
    load_user_account_by_username,
    update_user_account_active_status,
)
from user_service import register_user_account


class DeterministicAssistantProvider:
    def __init__(
        self,
        output="Deterministic assistant response.",
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


class TestAiAssistantService(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name)
            / "ai-assistant-service.db"
        )

        self.assertTrue(
            register_user_account(
                "AssistantAdmin",
                "SecureAdminPassword123!",
                "admin",
                self.database_file,
            )
        )
        self.assertTrue(
            register_user_account(
                "AssistantViewer",
                "SecureViewerPassword123!",
                "viewer",
                self.database_file,
            )
        )

        self.administrator = load_user_account_by_username(
            "AssistantAdmin",
            self.database_file,
        )
        self.viewer = load_user_account_by_username(
            "AssistantViewer",
            self.database_file,
        )

        self.assertIsNotNone(self.administrator)
        self.assertIsNotNone(self.viewer)

        if self.administrator is None:
            self.fail(
                "The AI Assistant administrator was not found."
            )

        if self.viewer is None:
            self.fail(
                "The AI Assistant viewer was not found."
            )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_administrator_receives_normalized_response(self):
        provider = DeterministicAssistantProvider(
            output="  Review the workflow schedule.  "
        )

        response = ask_ai_assistant(
            self.administrator,
            "  How should I review this workflow?  ",
            "  test-assistant-model  ",
            provider,
            self.database_file,
        )

        self.assertEqual(
            response,
            "Review the workflow schedule.",
        )
        self.assertEqual(
            provider.calls,
            [
                {
                    "model_name": "test-assistant-model",
                    "system_prompt": AI_ASSISTANT_SYSTEM_PROMPT,
                    "input_text": (
                        "How should I review this workflow?"
                    ),
                }
            ],
        )

    def test_viewer_cannot_use_ai_assistant(self):
        provider = DeterministicAssistantProvider()

        response = ask_ai_assistant(
            self.viewer,
            "Help with this workflow.",
            "test-assistant-model",
            provider,
            self.database_file,
        )

        self.assertIsNone(response)
        self.assertEqual(provider.calls, [])

    def test_deactivated_administrator_is_rejected(self):
        self.assertTrue(
            update_user_account_active_status(
                self.administrator["username"],
                False,
                self.database_file,
            )
        )
        provider = DeterministicAssistantProvider()

        response = ask_ai_assistant(
            self.administrator,
            "Help with this workflow.",
            "test-assistant-model",
            provider,
            self.database_file,
        )

        self.assertIsNone(response)
        self.assertEqual(provider.calls, [])

    def test_mismatched_session_identity_is_rejected(self):
        mismatched_administrator = dict(self.administrator)
        mismatched_administrator["user_id"] = (
            self.administrator["user_id"] + 1000
        )
        provider = DeterministicAssistantProvider()

        response = ask_ai_assistant(
            mismatched_administrator,
            "Help with this workflow.",
            "test-assistant-model",
            provider,
            self.database_file,
        )

        self.assertIsNone(response)
        self.assertEqual(provider.calls, [])

    def test_invalid_question_and_model_are_rejected_before_provider_call(
        self,
    ):
        invalid_requests = (
            {
                "question": "",
                "model_name": "test-assistant-model",
            },
            {
                "question": (
                    "x" * (MAX_AI_ASSISTANT_QUESTION_LENGTH + 1)
                ),
                "model_name": "test-assistant-model",
            },
            {
                "question": "Help with this workflow.",
                "model_name": "",
            },
            {
                "question": "Help with this workflow.",
                "model_name": (
                    "x"
                    * (
                        MAX_AI_ASSISTANT_MODEL_NAME_LENGTH
                        + 1
                    )
                ),
            },
        )

        for request in invalid_requests:
            with self.subTest(request=request):
                provider = DeterministicAssistantProvider()

                response = ask_ai_assistant(
                    self.administrator,
                    request["question"],
                    request["model_name"],
                    provider,
                    self.database_file,
                )

                self.assertIsNone(response)
                self.assertEqual(provider.calls, [])

    def test_provider_exception_becomes_safe_error_without_cause(self):
        unsafe_detail = (
            "provider failed with secret test-api-key"
        )
        provider = DeterministicAssistantProvider(
            error=RuntimeError(unsafe_detail)
        )

        with self.assertRaises(AgentProviderError) as context:
            ask_ai_assistant(
                self.administrator,
                "Help with this workflow.",
                "test-assistant-model",
                provider,
                self.database_file,
            )

        self.assertEqual(
            str(context.exception),
            SAFE_AI_ASSISTANT_ERROR_MESSAGE,
        )
        self.assertNotIn(
            unsafe_detail,
            str(context.exception),
        )
        self.assertIsNone(context.exception.__cause__)

    def test_invalid_provider_responses_become_safe_error(self):
        invalid_outputs = (
            None,
            "",
            "   ",
            "x" * (MAX_AI_ASSISTANT_RESPONSE_LENGTH + 1),
        )

        for output in invalid_outputs:
            with self.subTest(output=output):
                provider = DeterministicAssistantProvider(
                    output=output
                )

                with self.assertRaisesRegex(
                    AgentProviderError,
                    SAFE_AI_ASSISTANT_ERROR_MESSAGE,
                ):
                    ask_ai_assistant(
                        self.administrator,
                        "Help with this workflow.",
                        "test-assistant-model",
                        provider,
                        self.database_file,
                    )


if __name__ == "__main__":
    unittest.main()