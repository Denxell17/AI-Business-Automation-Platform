import unittest

from authorization import (
    EXECUTE_AGENT_TEMPLATES,
    user_has_permission,
)


class TestAgentExecutionAuthorization(unittest.TestCase):
    def setUp(self):
        self.administrator = {
            "user_id": 1,
            "username": "ExecutionAdmin",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        self.viewer = {
            "user_id": 2,
            "username": "ExecutionViewer",
            "password_hash": "protected_hash",
            "role": "viewer",
            "is_active": True,
        }

    def test_administrator_can_execute_agent_templates(
        self,
    ):
        self.assertTrue(
            user_has_permission(
                self.administrator,
                EXECUTE_AGENT_TEMPLATES,
            )
        )

    def test_viewer_cannot_execute_agent_templates(
        self,
    ):
        self.assertFalse(
            user_has_permission(
                self.viewer,
                EXECUTE_AGENT_TEMPLATES,
            )
        )

    def test_unknown_role_cannot_execute_agent_templates(
        self,
    ):
        unknown_user = {
            "user_id": 3,
            "username": "Unknown",
            "password_hash": "protected_hash",
            "role": "unknown",
            "is_active": True,
        }

        self.assertFalse(
            user_has_permission(
                unknown_user,
                EXECUTE_AGENT_TEMPLATES,
            )
        )


if __name__ == "__main__":
    unittest.main()