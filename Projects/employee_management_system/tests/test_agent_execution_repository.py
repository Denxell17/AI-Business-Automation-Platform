import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    complete_agent_execution,
    fail_agent_execution,
    insert_agent_execution,
    insert_agent_template,
    insert_user_account,
    load_agent_execution_by_id,
    load_agent_executions_for_template,
    load_user_account_by_username,
)
from models import AgentExecution


class TestAgentExecutionRepository(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name)
            / "agent-execution-repository.db"
        )

        user_created = insert_user_account(
            "AgentRepositoryAdmin",
            "protected_password_hash",
            "admin",
            self.database_file,
        )
        self.assertTrue(user_created)

        self.administrator = load_user_account_by_username(
            "AgentRepositoryAdmin",
            self.database_file,
        )
        self.assertIsNotNone(self.administrator)

        if self.administrator is None:
            self.fail(
                "The repository-test administrator was not found."
            )

        self.agent_template_id = "AGENT-REPOSITORY-TEST"
        self.started_at = "2026-09-11T01:00:00+00:00"
        self.finished_at = "2026-09-11T01:01:00+00:00"

        template_created = insert_agent_template(
            {
                "agent_template_id": self.agent_template_id,
                "name": "Repository Test Agent",
                "description": (
                    "Used by Agent Execution repository tests."
                ),
                "system_prompt": (
                    "Return a clear and accurate response."
                ),
                "model_name": "test-model",
                "status": "active",
                "created_by_user_id": self.administrator[
                    "user_id"
                ],
                "created_at": self.started_at,
                "updated_at": self.started_at,
            },
            self.database_file,
        )
        self.assertTrue(template_created)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def build_running_execution(
        self,
        agent_execution_id="EXEC-REPOSITORY-001",
        started_at=None,
    ) -> AgentExecution:
        return {
            "agent_execution_id": agent_execution_id,
            "agent_template_id": self.agent_template_id,
            "agent_template_name": "Repository Test Agent",
            "model_name": "test-model",
            "status": "running",
            "input_text": (
                "Summarize the latest customer request."
            ),
            "output_text": None,
            "error_message": None,
            "requested_by_user_id": self.administrator[
                "user_id"
            ],
            "started_at": (
                started_at
                if started_at is not None
                else self.started_at
            ),
            "finished_at": None,
        }

    def test_insert_and_load_agent_execution_by_id(self):
        execution = self.build_running_execution()

        inserted = insert_agent_execution(
            execution,
            self.database_file,
        )
        loaded = load_agent_execution_by_id(
            execution["agent_execution_id"],
            self.database_file,
        )

        self.assertTrue(inserted)
        self.assertEqual(loaded, execution)

    def test_duplicate_execution_id_is_rejected(self):
        execution = self.build_running_execution()

        first_insert = insert_agent_execution(
            execution,
            self.database_file,
        )
        duplicate_insert = insert_agent_execution(
            execution,
            self.database_file,
        )
        loaded = load_agent_execution_by_id(
            execution["agent_execution_id"],
            self.database_file,
        )

        self.assertTrue(first_insert)
        self.assertFalse(duplicate_insert)
        self.assertEqual(loaded, execution)

    def test_template_history_is_loaded_newest_first(self):
        older_execution = self.build_running_execution(
            agent_execution_id="EXEC-HISTORY-OLDER",
            started_at="2026-09-11T01:00:00+00:00",
        )
        newer_execution = self.build_running_execution(
            agent_execution_id="EXEC-HISTORY-NEWER",
            started_at="2026-09-11T02:00:00+00:00",
        )

        self.assertTrue(
            insert_agent_execution(
                older_execution,
                self.database_file,
            )
        )
        self.assertTrue(
            insert_agent_execution(
                newer_execution,
                self.database_file,
            )
        )

        history = load_agent_executions_for_template(
            self.agent_template_id,
            self.database_file,
        )

        self.assertEqual(
            [
                execution["agent_execution_id"]
                for execution in history
            ],
            [
                "EXEC-HISTORY-NEWER",
                "EXEC-HISTORY-OLDER",
            ],
        )

    def test_missing_and_empty_execution_history_are_safe(
        self,
    ):
        missing_execution = load_agent_execution_by_id(
            "EXEC-MISSING",
            self.database_file,
        )
        empty_history = load_agent_executions_for_template(
            "AGENT-WITHOUT-EXECUTIONS",
            self.database_file,
        )

        self.assertIsNone(missing_execution)
        self.assertEqual(empty_history, [])

    def test_running_execution_can_be_completed(self):
        execution = self.build_running_execution()
        self.assertTrue(
            insert_agent_execution(
                execution,
                self.database_file,
            )
        )

        completed = complete_agent_execution(
            execution["agent_execution_id"],
            "The customer requested an updated invoice.",
            self.finished_at,
            self.database_file,
        )
        loaded = load_agent_execution_by_id(
            execution["agent_execution_id"],
            self.database_file,
        )

        self.assertTrue(completed)
        self.assertIsNotNone(loaded)

        if loaded is None:
            self.fail(
                "The completed execution was not found."
            )

        self.assertEqual(loaded["status"], "completed")
        self.assertEqual(
            loaded["output_text"],
            "The customer requested an updated invoice.",
        )
        self.assertIsNone(loaded["error_message"])
        self.assertEqual(
            loaded["finished_at"],
            self.finished_at,
        )

    def test_running_execution_can_be_failed(self):
        execution = self.build_running_execution()
        self.assertTrue(
            insert_agent_execution(
                execution,
                self.database_file,
            )
        )

        failed = fail_agent_execution(
            execution["agent_execution_id"],
            "The AI provider was unavailable.",
            self.finished_at,
            self.database_file,
        )
        loaded = load_agent_execution_by_id(
            execution["agent_execution_id"],
            self.database_file,
        )

        self.assertTrue(failed)
        self.assertIsNotNone(loaded)

        if loaded is None:
            self.fail(
                "The failed execution was not found."
            )

        self.assertEqual(loaded["status"], "failed")
        self.assertIsNone(loaded["output_text"])
        self.assertEqual(
            loaded["error_message"],
            "The AI provider was unavailable.",
        )
        self.assertEqual(
            loaded["finished_at"],
            self.finished_at,
        )

    def test_invalid_or_missing_finalization_is_rejected(
        self,
    ):
        execution = self.build_running_execution()
        self.assertTrue(
            insert_agent_execution(
                execution,
                self.database_file,
            )
        )

        blank_completion = complete_agent_execution(
            execution["agent_execution_id"],
            "   ",
            self.finished_at,
            self.database_file,
        )
        blank_failure = fail_agent_execution(
            execution["agent_execution_id"],
            "   ",
            self.finished_at,
            self.database_file,
        )
        missing_completion = complete_agent_execution(
            "EXEC-MISSING",
            "Unused result.",
            self.finished_at,
            self.database_file,
        )
        missing_failure = fail_agent_execution(
            "EXEC-MISSING",
            "Unused error.",
            self.finished_at,
            self.database_file,
        )

        self.assertFalse(blank_completion)
        self.assertFalse(blank_failure)
        self.assertFalse(missing_completion)
        self.assertFalse(missing_failure)

        loaded = load_agent_execution_by_id(
            execution["agent_execution_id"],
            self.database_file,
        )
        self.assertEqual(loaded["status"], "running")

    def test_finalized_execution_cannot_change_state_again(
        self,
    ):
        execution = self.build_running_execution()
        self.assertTrue(
            insert_agent_execution(
                execution,
                self.database_file,
            )
        )

        first_completion = complete_agent_execution(
            execution["agent_execution_id"],
            "First and final result.",
            self.finished_at,
            self.database_file,
        )
        second_completion = complete_agent_execution(
            execution["agent_execution_id"],
            "Replacement result.",
            "2026-09-11T01:02:00+00:00",
            self.database_file,
        )
        later_failure = fail_agent_execution(
            execution["agent_execution_id"],
            "Replacement failure.",
            "2026-09-11T01:03:00+00:00",
            self.database_file,
        )

        loaded = load_agent_execution_by_id(
            execution["agent_execution_id"],
            self.database_file,
        )

        self.assertTrue(first_completion)
        self.assertFalse(second_completion)
        self.assertFalse(later_failure)
        self.assertEqual(loaded["status"], "completed")
        self.assertEqual(
            loaded["output_text"],
            "First and final result.",
        )
        self.assertIsNone(loaded["error_message"])
        self.assertEqual(
            loaded["finished_at"],
            self.finished_at,
        )


if __name__ == "__main__":
    unittest.main()