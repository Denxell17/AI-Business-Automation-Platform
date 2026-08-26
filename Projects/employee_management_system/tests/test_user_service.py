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


if __name__ == "__main__":
    unittest.main()