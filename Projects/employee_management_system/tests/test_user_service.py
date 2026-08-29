import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from authentication import verify_password
from database import (
    get_database_connection,
    load_user_account_by_username,
)
from user_service import (
    authenticate_user_account,
    register_initial_administrator,
    register_user_account,
    register_viewer_account,
    set_viewer_account_active_status,
    reset_viewer_account_password,
)


class TestUserService(unittest.TestCase):
    def test_register_user_account_hashes_password_before_storage(
        self,
    ):
        password = "SecurePassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            registration_result = register_user_account(
                "Dennis",
                password,
                "admin",
                database_file,
            )
            stored_user = load_user_account_by_username(
                "Dennis",
                database_file,
            )

            self.assertTrue(registration_result)
            self.assertIsNotNone(stored_user)

            if stored_user is None:
                self.fail("The registered user was not found.")

            self.assertNotEqual(
                stored_user["password_hash"],
                password,
            )
            self.assertTrue(
                verify_password(
                    password,
                    stored_user["password_hash"],
                )
            )

    def test_register_user_account_rejects_duplicate_username(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            first_result = register_user_account(
                "Dennis",
                "FirstPassword123!",
                "admin",
                database_file,
            )
            duplicate_result = register_user_account(
                "dennis",
                "SecondPassword123!",
                "viewer",
                database_file,
            )
            stored_user = load_user_account_by_username(
                "Dennis",
                database_file,
            )

            self.assertTrue(first_result)
            self.assertFalse(duplicate_result)
            self.assertIsNotNone(stored_user)

            if stored_user is None:
                self.fail("The original user was not found.")

            self.assertEqual(
                stored_user["username"],
                "Dennis",
            )
            self.assertEqual(
                stored_user["role"],
                "admin",
            )
            self.assertTrue(
                verify_password(
                    "FirstPassword123!",
                    stored_user["password_hash"],
                )
            )

    def test_authenticate_user_account_accepts_valid_credentials(
        self,
    ):
        password = "SecurePassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            registration_result = register_user_account(
                "Dennis",
                password,
                "admin",
                database_file,
            )
            authenticated_user = authenticate_user_account(
                "dennis",
                password,
                database_file,
            )

            self.assertTrue(registration_result)
            self.assertIsNotNone(authenticated_user)

            if authenticated_user is None:
                self.fail("Valid credentials were rejected.")

            self.assertEqual(
                authenticated_user["username"],
                "Dennis",
            )
            self.assertEqual(
                authenticated_user["role"],
                "admin",
            )
            self.assertTrue(
                authenticated_user["is_active"]
            )

    def test_authenticate_user_account_rejects_wrong_password(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            registration_result = register_user_account(
                "Dennis",
                "CorrectPassword123!",
                "admin",
                database_file,
            )
            authenticated_user = authenticate_user_account(
                "Dennis",
                "WrongPassword123!",
                database_file,
            )

            self.assertTrue(registration_result)
            self.assertIsNone(authenticated_user)

    def test_authenticate_user_account_rejects_missing_username(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            authenticated_user = authenticate_user_account(
                "UnknownUser",
                "SecurePassword123!",
                database_file,
            )

            self.assertIsNone(authenticated_user)
            self.assertTrue(database_file.exists())

    def test_authenticate_user_account_rejects_inactive_account(
        self,
    ):
        password = "SecurePassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            registration_result = register_user_account(
                "Dennis",
                password,
                "admin",
                database_file,
            )

            connection = get_database_connection(
                database_file
            )

            try:
                connection.execute(
                    """
                    UPDATE users
                    SET is_active = 0
                    WHERE username = ?
                    """,
                    ("Dennis",),
                )
                connection.commit()
            finally:
                connection.close()

            authenticated_user = authenticate_user_account(
                "Dennis",
                password,
                database_file,
            )

            self.assertTrue(registration_result)
            self.assertIsNone(authenticated_user)

    def test_register_initial_administrator_creates_first_account(
        self,
    ):
        password = "SecurePassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            registration_result = (
                register_initial_administrator(
                    "Dennis",
                    password,
                    database_file,
                )
            )
            stored_user = load_user_account_by_username(
                "Dennis",
                database_file,
            )

            self.assertTrue(registration_result)
            self.assertIsNotNone(stored_user)

            if stored_user is None:
                self.fail("The initial administrator was not found.")

            self.assertEqual(
                stored_user["role"],
                "admin",
            )
            self.assertTrue(
                stored_user["is_active"]
            )
            self.assertTrue(
                verify_password(
                    password,
                    stored_user["password_hash"],
                )
            )

    def test_register_initial_administrator_rejects_second_account(
        self,
    ):
        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            first_result = register_initial_administrator(
                "Dennis",
                "FirstAdminPassword123!",
                database_file,
            )
            second_result = register_initial_administrator(
                "AnotherAdmin",
                "SecondAdminPassword123!",
                database_file,
            )
            first_user = load_user_account_by_username(
                "Dennis",
                database_file,
            )
            second_user = load_user_account_by_username(
                "AnotherAdmin",
                database_file,
            )

            self.assertTrue(first_result)
            self.assertFalse(second_result)
            self.assertIsNotNone(first_user)
            self.assertIsNone(second_user)

    def test_administrator_can_register_viewer_account(self):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        password = "ViewerPassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            registration_result = register_viewer_account(
                administrator,
                "Analyst",
                password,
                database_file,
            )
            stored_viewer = load_user_account_by_username(
                "Analyst",
                database_file,
            )

            self.assertTrue(registration_result)
            self.assertIsNotNone(stored_viewer)

            if stored_viewer is None:
                self.fail("The viewer account was not found.")

            self.assertEqual(
                stored_viewer["role"],
                "viewer",
            )
            self.assertTrue(stored_viewer["is_active"])
            self.assertNotEqual(
                stored_viewer["password_hash"],
                password,
            )
            self.assertTrue(
                verify_password(
                    password,
                    stored_viewer["password_hash"],
                )
            )

    def test_viewer_cannot_register_viewer_account(self):
        viewer = {
            "user_id": 2,
            "username": "Viewer",
            "password_hash": "protected_hash",
            "role": "viewer",
            "is_active": True,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            registration_result = register_viewer_account(
                viewer,
                "BlockedUser",
                "BlockedPassword123!",
                database_file,
            )
            stored_user = load_user_account_by_username(
                "BlockedUser",
                database_file,
            )

            self.assertFalse(registration_result)
            self.assertIsNone(stored_user)

    def test_inactive_administrator_cannot_register_viewer_account(
        self,
    ):
        inactive_administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": False,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            registration_result = register_viewer_account(
                inactive_administrator,
                "BlockedUser",
                "BlockedPassword123!",
                database_file,
            )
            stored_user = load_user_account_by_username(
                "BlockedUser",
                database_file,
            )

            self.assertFalse(registration_result)
            self.assertIsNone(stored_user)

    def test_administrator_cannot_register_duplicate_viewer_username(
        self,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        original_password = "FirstViewerPassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            first_result = register_viewer_account(
                administrator,
                "Analyst",
                original_password,
                database_file,
            )
            duplicate_result = register_viewer_account(
                administrator,
                "analyst",
                "SecondViewerPassword123!",
                database_file,
            )
            stored_viewer = load_user_account_by_username(
                "Analyst",
                database_file,
            )

            self.assertTrue(first_result)
            self.assertFalse(duplicate_result)
            self.assertIsNotNone(stored_viewer)

            if stored_viewer is None:
                self.fail("The original viewer account was not found.")

            self.assertEqual(
                stored_viewer["username"],
                "Analyst",
            )
            self.assertEqual(
                stored_viewer["role"],
                "viewer",
            )
            self.assertTrue(
                verify_password(
                    original_password,
                    stored_viewer["password_hash"],
                )
            )
            self.assertFalse(
                verify_password(
                    "SecondViewerPassword123!",
                    stored_viewer["password_hash"],
                )
            )

    def test_administrator_can_deactivate_viewer_account(self):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            viewer_inserted = register_user_account(
                "ReportViewer",
                "ViewerPassword123!",
                "viewer",
                database_file,
            )
            status_changed = set_viewer_account_active_status(
                administrator,
                "ReportViewer",
                False,
                database_file,
            )
            stored_viewer = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(viewer_inserted)
            self.assertTrue(status_changed)
            self.assertIsNotNone(stored_viewer)

            if stored_viewer is None:
                self.fail("The viewer account was not found.")

            self.assertFalse(stored_viewer["is_active"])

    def test_administrator_can_reactivate_viewer_account(self):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            viewer_inserted = register_user_account(
                "ReportViewer",
                "ViewerPassword123!",
                "viewer",
                database_file,
            )
            deactivation_result = (
                set_viewer_account_active_status(
                    administrator,
                    "ReportViewer",
                    False,
                    database_file,
                )
            )
            reactivation_result = (
                set_viewer_account_active_status(
                    administrator,
                    "ReportViewer",
                    True,
                    database_file,
                )
            )
            stored_viewer = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(viewer_inserted)
            self.assertTrue(deactivation_result)
            self.assertTrue(reactivation_result)
            self.assertIsNotNone(stored_viewer)

            if stored_viewer is None:
                self.fail("The viewer account was not found.")

            self.assertTrue(stored_viewer["is_active"])

    def test_viewer_cannot_change_viewer_account_status(self):
        current_viewer = {
            "user_id": 2,
            "username": "CurrentViewer",
            "password_hash": "protected_hash",
            "role": "viewer",
            "is_active": True,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            target_inserted = register_user_account(
                "TargetViewer",
                "ViewerPassword123!",
                "viewer",
                database_file,
            )
            status_changed = set_viewer_account_active_status(
                current_viewer,
                "TargetViewer",
                False,
                database_file,
            )
            stored_target = load_user_account_by_username(
                "TargetViewer",
                database_file,
            )

            self.assertTrue(target_inserted)
            self.assertFalse(status_changed)
            self.assertIsNotNone(stored_target)

            if stored_target is None:
                self.fail("The target viewer account was not found.")

            self.assertTrue(stored_target["is_active"])

    def test_inactive_administrator_cannot_change_viewer_status(
        self,
    ):
        inactive_administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": False,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            target_inserted = register_user_account(
                "ReportViewer",
                "ViewerPassword123!",
                "viewer",
                database_file,
            )
            status_changed = set_viewer_account_active_status(
                inactive_administrator,
                "ReportViewer",
                False,
                database_file,
            )
            stored_target = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(target_inserted)
            self.assertFalse(status_changed)
            self.assertIsNotNone(stored_target)

            if stored_target is None:
                self.fail("The target viewer account was not found.")

            self.assertTrue(stored_target["is_active"])

    def test_administrator_cannot_change_administrator_status(
        self,
    ):
        current_administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            target_inserted = register_user_account(
                "SecondAdmin",
                "AdminPassword123!",
                "admin",
                database_file,
            )
            status_changed = set_viewer_account_active_status(
                current_administrator,
                "SecondAdmin",
                False,
                database_file,
            )
            stored_target = load_user_account_by_username(
                "SecondAdmin",
                database_file,
            )

            self.assertTrue(target_inserted)
            self.assertFalse(status_changed)
            self.assertIsNotNone(stored_target)

            if stored_target is None:
                self.fail("The target administrator was not found.")

            self.assertTrue(stored_target["is_active"])

    def test_administrator_cannot_change_missing_viewer_status(
        self,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            status_changed = set_viewer_account_active_status(
                administrator,
                "MissingViewer",
                False,
                database_file,
            )
            stored_target = load_user_account_by_username(
                "MissingViewer",
                database_file,
            )

            self.assertFalse(status_changed)
            self.assertIsNone(stored_target)

    def test_administrator_cannot_apply_unchanged_viewer_status(
        self,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            viewer_inserted = register_user_account(
                "ReportViewer",
                "ViewerPassword123!",
                "viewer",
                database_file,
            )
            status_changed = set_viewer_account_active_status(
                administrator,
                "ReportViewer",
                True,
                database_file,
            )
            stored_viewer = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(viewer_inserted)
            self.assertFalse(status_changed)
            self.assertIsNotNone(stored_viewer)

            if stored_viewer is None:
                self.fail("The viewer account was not found.")

            self.assertTrue(stored_viewer["is_active"])

    def test_administrator_can_reset_viewer_account_password(
        self,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        original_password = "OriginalPassword123!"
        replacement_password = "ReplacementPassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            viewer_inserted = register_user_account(
                "ReportViewer",
                original_password,
                "viewer",
                database_file,
            )
            password_reset = reset_viewer_account_password(
                administrator,
                "ReportViewer",
                replacement_password,
                database_file,
            )
            stored_viewer = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(viewer_inserted)
            self.assertTrue(password_reset)
            self.assertIsNotNone(stored_viewer)

            if stored_viewer is None:
                self.fail("The viewer account was not found.")

            self.assertFalse(
                verify_password(
                    original_password,
                    stored_viewer["password_hash"],
                )
            )
            self.assertTrue(
                verify_password(
                    replacement_password,
                    stored_viewer["password_hash"],
                )
            )
            self.assertEqual(
                stored_viewer["role"],
                "viewer",
            )
            self.assertTrue(stored_viewer["is_active"])

    def test_viewer_cannot_reset_viewer_account_password(
        self,
    ):
        current_viewer = {
            "user_id": 2,
            "username": "CurrentViewer",
            "password_hash": "protected_hash",
            "role": "viewer",
            "is_active": True,
        }
        original_password = "OriginalPassword123!"
        replacement_password = "ReplacementPassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            target_inserted = register_user_account(
                "ReportViewer",
                original_password,
                "viewer",
                database_file,
            )
            password_reset = reset_viewer_account_password(
                current_viewer,
                "ReportViewer",
                replacement_password,
                database_file,
            )
            stored_target = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(target_inserted)
            self.assertFalse(password_reset)
            self.assertIsNotNone(stored_target)

            if stored_target is None:
                self.fail("The target viewer account was not found.")

            self.assertTrue(
                verify_password(
                    original_password,
                    stored_target["password_hash"],
                )
            )
            self.assertFalse(
                verify_password(
                    replacement_password,
                    stored_target["password_hash"],
                )
            )

    def test_inactive_administrator_cannot_reset_viewer_password(
        self,
    ):
        inactive_administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": False,
        }
        original_password = "OriginalPassword123!"
        replacement_password = "ReplacementPassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            target_inserted = register_user_account(
                "ReportViewer",
                original_password,
                "viewer",
                database_file,
            )
            password_reset = reset_viewer_account_password(
                inactive_administrator,
                "ReportViewer",
                replacement_password,
                database_file,
            )
            stored_target = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(target_inserted)
            self.assertFalse(password_reset)
            self.assertIsNotNone(stored_target)

            if stored_target is None:
                self.fail("The target viewer account was not found.")

            self.assertTrue(
                verify_password(
                    original_password,
                    stored_target["password_hash"],
                )
            )
            self.assertFalse(
                verify_password(
                    replacement_password,
                    stored_target["password_hash"],
                )
            )

    def test_administrator_cannot_reset_administrator_password(
        self,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        original_password = "OriginalAdminPassword123!"
        replacement_password = "ReplacementPassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            administrator_inserted = register_user_account(
                "Dennis",
                original_password,
                "admin",
                database_file,
            )
            password_reset = reset_viewer_account_password(
                administrator,
                "Dennis",
                replacement_password,
                database_file,
            )
            stored_administrator = load_user_account_by_username(
                "Dennis",
                database_file,
            )

            self.assertTrue(administrator_inserted)
            self.assertFalse(password_reset)
            self.assertIsNotNone(stored_administrator)

            if stored_administrator is None:
                self.fail("The administrator account was not found.")

            self.assertTrue(
                verify_password(
                    original_password,
                    stored_administrator["password_hash"],
                )
            )
            self.assertFalse(
                verify_password(
                    replacement_password,
                    stored_administrator["password_hash"],
                )
            )

    def test_administrator_cannot_reset_missing_viewer_password(
        self,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            password_reset = reset_viewer_account_password(
                administrator,
                "MissingViewer",
                "ReplacementPassword123!",
                database_file,
            )
            stored_target = load_user_account_by_username(
                "MissingViewer",
                database_file,
            )

            self.assertFalse(password_reset)
            self.assertIsNone(stored_target)

    def test_administrator_cannot_reset_viewer_to_blank_password(
        self,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        original_password = "OriginalPassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            target_inserted = register_user_account(
                "ReportViewer",
                original_password,
                "viewer",
                database_file,
            )
            password_reset = reset_viewer_account_password(
                administrator,
                "ReportViewer",
                "   ",
                database_file,
            )
            stored_target = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(target_inserted)
            self.assertFalse(password_reset)
            self.assertIsNotNone(stored_target)

            if stored_target is None:
                self.fail("The target viewer account was not found.")

            self.assertTrue(
                verify_password(
                    original_password,
                    stored_target["password_hash"],
                )
            )

    def test_administrator_cannot_reuse_viewer_current_password(
        self,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        current_password = "CurrentPassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            target_inserted = register_user_account(
                "ReportViewer",
                current_password,
                "viewer",
                database_file,
            )
            viewer_before_reset = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(target_inserted)
            self.assertIsNotNone(viewer_before_reset)

            if viewer_before_reset is None:
                self.fail("The viewer account was not found.")

            password_reset = reset_viewer_account_password(
                administrator,
                "ReportViewer",
                current_password,
                database_file,
            )
            viewer_after_reset = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertFalse(password_reset)
            self.assertIsNotNone(viewer_after_reset)

            if viewer_after_reset is None:
                self.fail("The viewer account was not found.")

            self.assertEqual(
                viewer_after_reset["password_hash"],
                viewer_before_reset["password_hash"],
            )
            self.assertTrue(
                verify_password(
                    current_password,
                    viewer_after_reset["password_hash"],
                )
            )

    def test_administrator_can_reset_inactive_viewer_password(
        self,
    ):
        administrator = {
            "user_id": 1,
            "username": "Dennis",
            "password_hash": "protected_hash",
            "role": "admin",
            "is_active": True,
        }
        original_password = "OriginalPassword123!"
        replacement_password = "ReplacementPassword123!"

        with TemporaryDirectory() as temporary_directory:
            database_file = (
                Path(temporary_directory) / "employees.db"
            )

            target_inserted = register_user_account(
                "ReportViewer",
                original_password,
                "viewer",
                database_file,
            )
            deactivation_result = (
                set_viewer_account_active_status(
                    administrator,
                    "ReportViewer",
                    False,
                    database_file,
                )
            )
            password_reset = reset_viewer_account_password(
                administrator,
                "ReportViewer",
                replacement_password,
                database_file,
            )
            stored_target = load_user_account_by_username(
                "ReportViewer",
                database_file,
            )

            self.assertTrue(target_inserted)
            self.assertTrue(deactivation_result)
            self.assertTrue(password_reset)
            self.assertIsNotNone(stored_target)

            if stored_target is None:
                self.fail("The target viewer account was not found.")

            self.assertFalse(stored_target["is_active"])
            self.assertFalse(
                verify_password(
                    original_password,
                    stored_target["password_hash"],
                )
            )
            self.assertTrue(
                verify_password(
                    replacement_password,
                    stored_target["password_hash"],
                )
            )


if __name__ == "__main__":
    unittest.main()