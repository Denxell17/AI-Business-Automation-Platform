import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_execution_service import (
    MAX_AGENT_EXECUTION_INPUT_LENGTH,
    MAX_AGENT_EXECUTION_OUTPUT_LENGTH,
    SAFE_AGENT_PROVIDER_ERROR_MESSAGE,
    execute_agent_template,
)
from agent_provider import AgentProviderError
from database import (
    insert_agent_template,
    load_agent_executions_for_template,
    load_user_account_by_username,
    update_user_account_active_status,
)
from user_service import register_user_account


class DeterministicAgentProvider:
    def __init__(
        self,
        output="Deterministic provider response.",
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


class TestAgentExecutionService(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name)
            / "agent-execution-service.db"
        )

        administrator_created = register_user_account(
            "AgentExecutionAdmin",
            "SecurePassword123!",
            "admin",
            self.database_file,
        )
        viewer_created = register_user_account(
            "AgentExecutionViewer",
            "SecurePassword123!",
            "viewer",
            self.database_file,
        )

        self.assertTrue(administrator_created)
        self.assertTrue(viewer_created)

        self.administrator = load_user_account_by_username(
            "AgentExecutionAdmin",
            self.database_file,
        )
        self.viewer = load_user_account_by_username(
            "AgentExecutionViewer",
            self.database_file,
        )

        self.assertIsNotNone(self.administrator)
        self.assertIsNotNone(self.viewer)

        if self.administrator is None:
            self.fail(
                "The execution-test administrator was not found."
            )

        if self.viewer is None:
            self.fail(
                "The execution-test viewer was not found."
            )

        self.active_template_id = "AGENT-EXECUTION-ACTIVE"
        self.draft_template_id = "AGENT-EXECUTION-DRAFT"
        self.system_prompt = (
            "Respond clearly and protect customer information."
        )
        self.timestamp = "2026-09-11T02:00:00+00:00"

        self.create_template(
            self.active_template_id,
            "Active Execution Agent",
            "active",
        )
        self.create_template(
            self.draft_template_id,
            "Draft Execution Agent",
            "draft",
        )

    def tearDown(self):
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
                    "Used by Agent Execution service tests."
                ),
                "system_prompt": self.system_prompt,
                "model_name": "deterministic-model",
                "status": status,
                "created_by_user_id": self.administrator[
                    "user_id"
                ],
                "created_at": self.timestamp,
                "updated_at": self.timestamp,
            },
            self.database_file,
        )
        self.assertTrue(inserted)

    def test_administrator_executes_active_template(
        self,
    ):
        provider = DeterministicAgentProvider(
            output="  Completed deterministic response.  "
        )

        execution = execute_agent_template(
            self.administrator,
            self.active_template_id.lower(),
            "  Summarize this customer request.  ",
            provider,
            self.database_file,
        )

        self.assertIsNotNone(execution)

        if execution is None:
            self.fail(
                "The successful execution was not returned."
            )

        self.assertTrue(
            execution["agent_execution_id"].startswith(
                "AGENT-EXEC-"
            )
        )
        self.assertEqual(
            execution["agent_template_id"],
            self.active_template_id,
        )
        self.assertEqual(
            execution["agent_template_name"],
            "Active Execution Agent",
        )
        self.assertEqual(
            execution["model_name"],
            "deterministic-model",
        )
        self.assertEqual(execution["status"], "completed")
        self.assertEqual(
            execution["input_text"],
            "Summarize this customer request.",
        )
        self.assertEqual(
            execution["output_text"],
            "Completed deterministic response.",
        )
        self.assertIsNone(execution["error_message"])
        self.assertIsNotNone(execution["finished_at"])

        self.assertEqual(
            provider.calls,
            [
                {
                    "model_name": "deterministic-model",
                    "system_prompt": self.system_prompt,
                    "input_text": (
                        "Summarize this customer request."
                    ),
                }
            ],
        )

    def test_draft_template_cannot_be_executed(self):
        provider = DeterministicAgentProvider()

        execution = execute_agent_template(
            self.administrator,
            self.draft_template_id,
            "Attempt to execute a Draft template.",
            provider,
            self.database_file,
        )

        self.assertIsNone(execution)
        self.assertEqual(provider.calls, [])
        self.assertEqual(
            load_agent_executions_for_template(
                self.draft_template_id,
                self.database_file,
            ),
            [],
        )

    def test_viewer_cannot_execute_agent_template(self):
        provider = DeterministicAgentProvider()

        execution = execute_agent_template(
            self.viewer,
            self.active_template_id,
            "Unauthorized viewer request.",
            provider,
            self.database_file,
        )

        self.assertIsNone(execution)
        self.assertEqual(provider.calls, [])
        self.assertEqual(
            load_agent_executions_for_template(
                self.active_template_id,
                self.database_file,
            ),
            [],
        )

    def test_deactivated_administrator_is_rejected(self):
        deactivated = update_user_account_active_status(
            self.administrator["username"],
            False,
            self.database_file,
        )
        self.assertTrue(deactivated)

        provider = DeterministicAgentProvider()

        execution = execute_agent_template(
            self.administrator,
            self.active_template_id,
            "Request from a stale active session.",
            provider,
            self.database_file,
        )

        self.assertIsNone(execution)
        self.assertEqual(provider.calls, [])

    def test_mismatched_session_identity_is_rejected(
        self,
    ):
        mismatched_user = dict(self.administrator)
        mismatched_user["user_id"] += 1000
        provider = DeterministicAgentProvider()

        execution = execute_agent_template(
            mismatched_user,
            self.active_template_id,
            "Request from a mismatched session.",
            provider,
            self.database_file,
        )

        self.assertIsNone(execution)
        self.assertEqual(provider.calls, [])

    def test_invalid_input_is_rejected_before_provider_call(
        self,
    ):
        invalid_inputs = (
            "",
            "   ",
            "x" * (
                MAX_AGENT_EXECUTION_INPUT_LENGTH + 1
            ),
        )

        for input_text in invalid_inputs:
            with self.subTest(input_length=len(input_text)):
                provider = DeterministicAgentProvider()

                execution = execute_agent_template(
                    self.administrator,
                    self.active_template_id,
                    input_text,
                    provider,
                    self.database_file,
                )

                self.assertIsNone(execution)
                self.assertEqual(provider.calls, [])

        self.assertEqual(
            load_agent_executions_for_template(
                self.active_template_id,
                self.database_file,
            ),
            [],
        )

    def test_provider_exception_creates_safe_failed_record(
        self,
    ):
        sensitive_error = (
            "Secret provider token and internal details."
        )
        provider = DeterministicAgentProvider(
            error=AgentProviderError(sensitive_error)
        )

        execution = execute_agent_template(
            self.administrator,
            self.active_template_id,
            "Generate a protected response.",
            provider,
            self.database_file,
        )

        self.assertIsNotNone(execution)

        if execution is None:
            self.fail(
                "The failed execution was not returned."
            )

        self.assertEqual(execution["status"], "failed")
        self.assertIsNone(execution["output_text"])
        self.assertEqual(
            execution["error_message"],
            SAFE_AGENT_PROVIDER_ERROR_MESSAGE,
        )
        self.assertNotIn(
            sensitive_error,
            execution["error_message"],
        )
        self.assertIsNotNone(execution["finished_at"])
        self.assertEqual(len(provider.calls), 1)

    def test_invalid_provider_outputs_create_failed_records(
        self,
    ):
        invalid_outputs = (
            "",
            "   ",
            None,
            123,
            "x" * (
                MAX_AGENT_EXECUTION_OUTPUT_LENGTH + 1
            ),
        )

        for provider_output in invalid_outputs:
            with self.subTest(
                provider_output_type=type(
                    provider_output
                ).__name__
            ):
                provider = DeterministicAgentProvider(
                    output=provider_output
                )

                execution = execute_agent_template(
                    self.administrator,
                    self.active_template_id,
                    "Test an invalid provider response.",
                    provider,
                    self.database_file,
                )

                self.assertIsNotNone(execution)

                if execution is None:
                    self.fail(
                        "The invalid provider response did "
                        "not produce a Failed record."
                    )

                self.assertEqual(
                    execution["status"],
                    "failed",
                )
                self.assertIsNone(
                    execution["output_text"]
                )
                self.assertEqual(
                    execution["error_message"],
                    SAFE_AGENT_PROVIDER_ERROR_MESSAGE,
                )
                self.assertIsNotNone(
                    execution["finished_at"]
                )

        history = load_agent_executions_for_template(
            self.active_template_id,
            self.database_file,
        )
        self.assertEqual(len(history), len(invalid_outputs))


if __name__ == "__main__":
    unittest.main()