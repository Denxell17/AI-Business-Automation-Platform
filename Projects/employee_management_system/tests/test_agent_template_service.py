import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_template_service import (
    MAX_AGENT_TEMPLATE_DESCRIPTION_LENGTH,
    MAX_AGENT_TEMPLATE_NAME_LENGTH,
    create_agent_template,
)
from database import (
    load_agent_template_by_id,
    load_agent_templates_from_database,
    load_user_account_by_username,
    update_user_account_active_status,
)
from user_service import register_user_account


class TestAgentTemplateService(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name) / "employees.db"
        )

        administrator_created = register_user_account(
            "AgentServiceAdmin",
            "SecurePassword123!",
            "admin",
            self.database_file,
        )
        viewer_created = register_user_account(
            "AgentServiceViewer",
            "SecurePassword123!",
            "viewer",
            self.database_file,
        )

        self.assertTrue(administrator_created)
        self.assertTrue(viewer_created)

        self.administrator = load_user_account_by_username(
            "AgentServiceAdmin",
            self.database_file,
        )
        self.viewer = load_user_account_by_username(
            "AgentServiceViewer",
            self.database_file,
        )

        self.assertIsNotNone(self.administrator)
        self.assertIsNotNone(self.viewer)

        if self.administrator is None:
            self.fail(
                "The agent-template administrator was not found."
            )

        if self.viewer is None:
            self.fail(
                "The agent-template viewer was not found."
            )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def submit_template(
        self,
        current_user=None,
        **overrides,
    ) -> bool:
        values = {
            "agent_template_id": "AGENT-000001",
            "name": "Customer Support Assistant",
            "description": (
                "Helps prepare customer-support responses."
            ),
            "system_prompt": (
                "Respond clearly and protect customer data."
            ),
            "model_name": "gpt-5.6-terra",
            "status": "draft",
        }
        values.update(overrides)

        selected_user = (
            self.administrator
            if current_user is None
            else current_user
        )

        return create_agent_template(
            selected_user,
            values["agent_template_id"],
            values["name"],
            values["description"],
            values["system_prompt"],
            values["model_name"],
            values["status"],
            self.database_file,
        )

    def test_administrator_creates_normalized_draft_template(
        self,
    ):
        created = self.submit_template(
            agent_template_id=" agent-000001 ",
            name=" Customer Support Assistant ",
            description=" Prepare safe responses. ",
            system_prompt=(
                " Respond clearly and protect customer data. "
            ),
            model_name=" gpt-5.6-terra ",
            status=" DRAFT ",
        )
        stored_template = load_agent_template_by_id(
            "AGENT-000001",
            self.database_file,
        )

        self.assertTrue(created)
        self.assertIsNotNone(stored_template)

        if stored_template is None:
            self.fail("The created template was not found.")

        self.assertEqual(
            stored_template["agent_template_id"],
            "AGENT-000001",
        )
        self.assertEqual(
            stored_template["name"],
            "Customer Support Assistant",
        )
        self.assertEqual(
            stored_template["description"],
            "Prepare safe responses.",
        )
        self.assertEqual(
            stored_template["system_prompt"],
            "Respond clearly and protect customer data.",
        )
        self.assertEqual(
            stored_template["model_name"],
            "gpt-5.6-terra",
        )
        self.assertEqual(
            stored_template["status"],
            "draft",
        )
        self.assertEqual(
            stored_template["created_by_user_id"],
            self.administrator["user_id"],
        )
        self.assertEqual(
            stored_template["created_at"],
            stored_template["updated_at"],
        )
        self.assertTrue(
            stored_template["created_at"].endswith("+00:00")
        )

    def test_viewer_cannot_create_agent_template(self):
        created = self.submit_template(
            current_user=self.viewer,
        )

        self.assertFalse(created)
        self.assertEqual(
            load_agent_templates_from_database(
                self.database_file
            ),
            [],
        )

    def test_deactivated_administrator_is_rejected(self):
        deactivated = update_user_account_active_status(
            self.administrator["username"],
            False,
            self.database_file,
        )
        created = self.submit_template()

        self.assertTrue(deactivated)
        self.assertFalse(created)
        self.assertEqual(
            load_agent_templates_from_database(
                self.database_file
            ),
            [],
        )

    def test_mismatched_session_identity_is_rejected(self):
        mismatched_user = self.administrator.copy()
        mismatched_user["user_id"] += 1000

        created = self.submit_template(
            current_user=mismatched_user,
        )

        self.assertFalse(created)
        self.assertEqual(
            load_agent_templates_from_database(
                self.database_file
            ),
            [],
        )

    def test_invalid_template_input_is_rejected(self):
        invalid_cases = [
            (
                "blank ID",
                {"agent_template_id": "   "},
            ),
            (
                "blank name",
                {"name": "   "},
            ),
            (
                "blank system prompt",
                {"system_prompt": "   "},
            ),
            (
                "blank model name",
                {"model_name": "   "},
            ),
            (
                "active initial status",
                {"status": "active"},
            ),
            (
                "inactive initial status",
                {"status": "inactive"},
            ),
            (
                "unknown status",
                {"status": "unknown"},
            ),
            (
                "name too long",
                {
                    "name": (
                        "A"
                        * (
                            MAX_AGENT_TEMPLATE_NAME_LENGTH
                            + 1
                        )
                    )
                },
            ),
            (
                "description too long",
                {
                    "description": (
                        "A"
                        * (
                            MAX_AGENT_TEMPLATE_DESCRIPTION_LENGTH
                            + 1
                        )
                    )
                },
            ),
            (
                "non-text system prompt",
                {"system_prompt": None},
            ),
        ]

        for case_name, overrides in invalid_cases:
            with self.subTest(case=case_name):
                created = self.submit_template(
                    **overrides
                )

                self.assertFalse(created)

        self.assertEqual(
            load_agent_templates_from_database(
                self.database_file
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()