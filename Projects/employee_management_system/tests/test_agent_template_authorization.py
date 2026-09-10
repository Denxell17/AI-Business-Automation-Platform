import unittest

from authorization import (
    MANAGE_AGENT_TEMPLATES,
    VIEW_AGENT_TEMPLATES,
    user_has_permission,
)


class TestAgentTemplateAuthorization(unittest.TestCase):
    def setUp(self):
        self.administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        self.viewer = {
            "user_id": 2,
            "username": "Viewer",
            "password_hash": "protected_hash",
            "role": "viewer",
            "is_active": True,
        }

    def test_administrator_can_manage_and_view_templates(self):
        self.assertTrue(
            user_has_permission(
                self.administrator,
                MANAGE_AGENT_TEMPLATES,
            )
        )
        self.assertTrue(
            user_has_permission(
                self.administrator,
                VIEW_AGENT_TEMPLATES,
            )
        )

    def test_viewer_can_view_but_cannot_manage_templates(self):
        self.assertTrue(
            user_has_permission(
                self.viewer,
                VIEW_AGENT_TEMPLATES,
            )
        )
        self.assertFalse(
            user_has_permission(
                self.viewer,
                MANAGE_AGENT_TEMPLATES,
            )
        )

    def test_unknown_role_has_no_template_permissions(self):
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
                VIEW_AGENT_TEMPLATES,
            )
        )
        self.assertFalse(
            user_has_permission(
                unknown_user,
                MANAGE_AGENT_TEMPLATES,
            )
        )


if __name__ == "__main__":
    unittest.main()