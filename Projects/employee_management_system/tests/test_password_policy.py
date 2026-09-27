import unittest

from password_policy import (
    MAXIMUM_PASSWORD_LENGTH,
    MINIMUM_PASSWORD_LENGTH,
    password_is_safe_to_verify,
    password_meets_policy,
)


class TestPasswordPolicy(unittest.TestCase):
    def test_accepts_long_passphrases_and_password_manager_output(self):
        self.assertTrue(
            password_meets_policy(
                "Dennis",
                "correct horse battery staple with spaces",
            )
        )
        self.assertTrue(
            password_meets_policy(
                "Dennis",
                "v3ry-L0ng!generated#password%2026",
            )
        )

    def test_enforces_minimum_and_maximum_length(self):
        self.assertFalse(
            password_meets_policy(
                "Dennis",
                "a" * (MINIMUM_PASSWORD_LENGTH - 1),
            )
        )
        self.assertTrue(
            password_meets_policy(
                "Dennis",
                "a" * MINIMUM_PASSWORD_LENGTH,
            )
        )
        self.assertTrue(
            password_meets_policy(
                "Dennis",
                "a" * MAXIMUM_PASSWORD_LENGTH,
            )
        )
        self.assertFalse(
            password_meets_policy(
                "Dennis",
                "a" * (MAXIMUM_PASSWORD_LENGTH + 1),
            )
        )

    def test_rejects_common_and_obvious_username_passwords(self):
        self.assertFalse(password_meets_policy("Dennis", "PASSWORD123456"))
        self.assertFalse(password_meets_policy("Dennis", "DennisPassword123!"))
        self.assertFalse(password_meets_policy("LongAccountName", "longaccountname"))

    def test_does_not_apply_fuzzy_or_composition_rules(self):
        self.assertTrue(password_meets_policy("Dennis", "dennis-is-a-long-passphrase"))
        self.assertTrue(password_meets_policy("Dennis", "alllowercasewordsareaccepted"))

    def test_rejects_control_characters(self):
        self.assertFalse(password_meets_policy("Dennis", "valid-looking\npassword"))
        self.assertFalse(password_meets_policy("Dennis", "valid-looking\tpassword"))

    def test_login_verification_bound_matches_policy_maximum(self):
        self.assertTrue(password_is_safe_to_verify("a" * MAXIMUM_PASSWORD_LENGTH))
        self.assertFalse(
            password_is_safe_to_verify("a" * (MAXIMUM_PASSWORD_LENGTH + 1))
        )


if __name__ == "__main__":
    unittest.main()
