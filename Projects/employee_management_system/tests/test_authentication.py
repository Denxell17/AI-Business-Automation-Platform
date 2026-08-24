import unittest

from authentication import (
    hash_password,
    verify_password,
)


class TestPasswordAuthentication(unittest.TestCase):
    def test_hash_password_returns_protected_storage_format(self):
        password = "SecurePassword123!"

        stored_password_hash = hash_password(password)
        hash_parts = stored_password_hash.split("$")

        self.assertEqual(len(hash_parts), 4)
        self.assertEqual(hash_parts[0], "sha256")
        self.assertEqual(hash_parts[1], "600000")
        self.assertEqual(len(hash_parts[2]), 32)
        self.assertEqual(len(hash_parts[3]), 64)
        self.assertNotIn(password, stored_password_hash)

    def test_same_password_creates_different_hashes(self):
        password = "SecurePassword123!"

        first_hash = hash_password(password)
        second_hash = hash_password(password)

        self.assertNotEqual(first_hash, second_hash)

    def test_verify_password_accepts_correct_password(self):
        password = "SecurePassword123!"

        stored_password_hash = hash_password(password)
        password_is_correct = verify_password(
            password,
            stored_password_hash,
        )

        self.assertTrue(password_is_correct)

    def test_verify_password_rejects_incorrect_password(self):
        stored_password_hash = hash_password(
            "SecurePassword123!"
        )

        password_is_correct = verify_password(
            "WrongPassword123!",
            stored_password_hash,
        )

        self.assertFalse(password_is_correct)

    def test_verify_password_rejects_malformed_hash(self):
        password_is_correct = verify_password(
            "SecurePassword123!",
            "Invalid_stored_hash",
        )

        self.assertFalse(password_is_correct)


if __name__ == "__main__":
    unittest.main()