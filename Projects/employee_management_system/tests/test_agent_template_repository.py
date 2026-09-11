import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from database import (
    insert_agent_template,
    load_agent_template_by_id,
    load_agent_templates_from_database,
    load_user_account_by_username,
    update_agent_template_in_database,
)
from user_service import register_user_account


TEST_TIMESTAMP = "2026-09-10T00:00:00+00:00"


class TestAgentTemplateRepository(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        self.database_file = (
            Path(self.temporary_directory.name) / "employees.db"
        )

        user_created = register_user_account(
            "AgentRepositoryAdmin",
            "SecurePassword123!",
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
                "The agent-template administrator was not found."
            )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def build_template(
        self,
        agent_template_id: str,
        name: str,
        status: str = "draft",
    ):
        return {
            "agent_template_id": agent_template_id,
            "name": name,
            "description": (
                f"Description for {name}."
            ),
            "system_prompt": (
                f"You are the {name} agent."
            ),
            "model_name": "gpt-5.6-terra",
            "status": status,
            "created_by_user_id": self.administrator[
                "user_id"
            ],
            "created_at": TEST_TIMESTAMP,
            "updated_at": TEST_TIMESTAMP,
        }

    def test_insert_and_load_agent_template_by_id(self):
        agent_template = self.build_template(
            "AGENT-000001",
            "Customer Support Assistant",
        )

        inserted = insert_agent_template(
            agent_template,
            self.database_file,
        )
        stored_template = load_agent_template_by_id(
            "AGENT-000001",
            self.database_file,
        )

        self.assertTrue(inserted)
        self.assertEqual(
            stored_template,
            agent_template,
        )

    def test_loading_returns_templates_in_name_order(self):
        second_template = self.build_template(
            "AGENT-000002",
            "Billing Assistant",
            "active",
        )
        first_template = self.build_template(
            "AGENT-000001",
            "appointment Assistant",
            "draft",
        )

        self.assertTrue(
            insert_agent_template(
                second_template,
                self.database_file,
            )
        )
        self.assertTrue(
            insert_agent_template(
                first_template,
                self.database_file,
            )
        )

        stored_templates = (
            load_agent_templates_from_database(
                self.database_file
            )
        )

        self.assertEqual(
            [
                template["agent_template_id"]
                for template in stored_templates
            ],
            [
                "AGENT-000001",
                "AGENT-000002",
            ],
        )

    def test_duplicate_id_is_rejected_without_replacing_record(
        self,
    ):
        original_template = self.build_template(
            "AGENT-000001",
            "Original Assistant",
        )
        duplicate_template = self.build_template(
            "AGENT-000001",
            "Replacement Assistant",
        )

        first_inserted = insert_agent_template(
            original_template,
            self.database_file,
        )
        duplicate_inserted = insert_agent_template(
            duplicate_template,
            self.database_file,
        )
        stored_template = load_agent_template_by_id(
            "AGENT-000001",
            self.database_file,
        )

        self.assertTrue(first_inserted)
        self.assertFalse(duplicate_inserted)
        self.assertEqual(
            stored_template,
            original_template,
        )

    def test_update_changes_editable_fields_and_status(self):
        original_template = self.build_template(
            "AGENT-000001",
            "Original Assistant",
        )

        self.assertTrue(
            insert_agent_template(
                original_template,
                self.database_file,
            )
        )

        updated_template = original_template.copy()
        updated_template.update(
            {
                "name": "Updated Assistant",
                "description": "Updated description.",
                "system_prompt": (
                    "Follow the updated system instructions."
                ),
                "model_name": "gpt-6-astra",
                "status": "active",
                "updated_at": (
                    "2026-09-11T01:00:00+00:00"
                ),
            }
        )

        updated = update_agent_template_in_database(
            updated_template,
            "draft",
            self.database_file,
        )
        stored_template = load_agent_template_by_id(
            "AGENT-000001",
            self.database_file,
        )

        self.assertTrue(updated)
        self.assertEqual(
            stored_template,
            updated_template,
        )
        self.assertEqual(
            stored_template["created_by_user_id"],
            original_template["created_by_user_id"],
        )
        self.assertEqual(
            stored_template["created_at"],
            original_template["created_at"],
        )

    def test_update_rejects_stale_expected_status(self):
        original_template = self.build_template(
            "AGENT-000001",
            "Original Assistant",
        )

        self.assertTrue(
            insert_agent_template(
                original_template,
                self.database_file,
            )
        )

        attempted_update = original_template.copy()
        attempted_update.update(
            {
                "name": "Stale Update",
                "status": "active",
                "updated_at": (
                    "2026-09-11T01:00:00+00:00"
                ),
            }
        )

        updated = update_agent_template_in_database(
            attempted_update,
            "active",
            self.database_file,
        )
        stored_template = load_agent_template_by_id(
            "AGENT-000001",
            self.database_file,
        )

        self.assertFalse(updated)
        self.assertEqual(
            stored_template,
            original_template,
        )

    def test_empty_and_missing_templates_are_safe(self):
        stored_templates = (
            load_agent_templates_from_database(
                self.database_file
            )
        )
        missing_template = load_agent_template_by_id(
            "AGENT-MISSING",
            self.database_file,
        )

        self.assertEqual(stored_templates, [])
        self.assertIsNone(missing_template)


if __name__ == "__main__":
    unittest.main()