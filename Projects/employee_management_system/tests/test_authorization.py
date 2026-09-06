import unittest

from authorization import (
    BACKUP_DATABASE,
    DELETE_EMPLOYEE,
    EXPORT_REPORT,
    MANAGE_USER_ACCOUNTS,
    MANAGE_WORKFLOWS,
    VIEW_WORKFLOWS,
    REGISTER_EMPLOYEE,
    RESTORE_DATABASE,
    UPDATE_EMPLOYEE,
    VIEW_EMPLOYEE,
    VIEW_PAYROLL,
    user_has_permission,
    VIEW_ACTIVITY_LOG,
)


class TestUserAuthorization(unittest.TestCase):
    def test_administrator_has_all_permissions(self):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        permissions = [
            REGISTER_EMPLOYEE,
            VIEW_EMPLOYEE,
            VIEW_PAYROLL,
            UPDATE_EMPLOYEE,
            DELETE_EMPLOYEE,
            EXPORT_REPORT,
            MANAGE_USER_ACCOUNTS,
            VIEW_WORKFLOWS,
            BACKUP_DATABASE,
            RESTORE_DATABASE,
            VIEW_ACTIVITY_LOG,
        ]

        for permission in permissions:
            with self.subTest(permission=permission):
                self.assertTrue(
                    user_has_permission(
                        administrator,
                        permission,
                    )
                )

    def test_viewer_has_only_read_only_permissions(self):
        viewer = {
            "user_id": 2,
            "username": "Viewer",
            "password_hash": "protected_hash",
            "role": "viewer",
            "is_active": True,
        }
        allowed_permissions = [
            VIEW_EMPLOYEE,
            VIEW_PAYROLL,
            EXPORT_REPORT,
            VIEW_WORKFLOWS,
        ]
        denied_permissions = [
            REGISTER_EMPLOYEE,
            UPDATE_EMPLOYEE,
            DELETE_EMPLOYEE,
            BACKUP_DATABASE,
            RESTORE_DATABASE,
            MANAGE_USER_ACCOUNTS,
            MANAGE_WORKFLOWS,
            VIEW_ACTIVITY_LOG,
        ]

        for permission in allowed_permissions:
            with self.subTest(
                permission=permission,
                expected="allowed",
            ):
                self.assertTrue(
                    user_has_permission(
                        viewer,
                        permission,
                    )
                )

        for permission in denied_permissions:
            with self.subTest(
                permission=permission,
                expected="denied",
            ):
                self.assertFalse(
                    user_has_permission(
                        viewer,
                        permission,
                    )
                )

    def test_workflow_management_is_administrator_only(self):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        viewer = {
            "user_id": 2,
            "username": "Viewer",
            "password_hash": "protected_hash",
            "role": "viewer",
            "is_active": True,
        }

        self.assertTrue(
            user_has_permission(
                administrator,
                MANAGE_WORKFLOWS,
            )
        )
        self.assertFalse(
            user_has_permission(
                viewer,
                MANAGE_WORKFLOWS,
            )
        )

    def test_workflow_viewing_is_available_to_admins_and_viewers(
        self,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        viewer = {
            "user_id": 2,
            "username": "Viewer",
            "password_hash": "protected_hash",
            "role": "viewer",
            "is_active": True,
        }

        self.assertTrue(
            user_has_permission(
                administrator,
                VIEW_WORKFLOWS,
            )
        )
        self.assertTrue(
            user_has_permission(
                viewer,
                VIEW_WORKFLOWS,
            )
        )

    def test_unknown_role_has_no_permissions(self):
        unknown_user = {
            "user_id": 3,
            "username": "Unknown",
            "password_hash": "protected_hash",
            "role": "unknown",
            "is_active": True,
        }
        permissions = [
            REGISTER_EMPLOYEE,
            VIEW_EMPLOYEE,
            VIEW_PAYROLL,
            UPDATE_EMPLOYEE,
            DELETE_EMPLOYEE,
            EXPORT_REPORT,
            BACKUP_DATABASE,
            RESTORE_DATABASE,
            MANAGE_USER_ACCOUNTS,
            VIEW_WORKFLOWS,
            VIEW_ACTIVITY_LOG,
        ]

        for permission in permissions:
            with self.subTest(permission=permission):
                self.assertFalse(
                    user_has_permission(
                        unknown_user,
                        permission,
                    )
                )

    def test_unknown_permission_is_denied(self):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }

        permission_is_allowed = user_has_permission(
            administrator,
            "unknown.permission",
        )

        self.assertFalse(permission_is_allowed)


if __name__ == "__main__":
    unittest.main()