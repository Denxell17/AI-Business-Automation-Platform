import unittest

from database_config import load_database_settings


class TestDatabaseConfiguration(unittest.TestCase):
    def test_sqlite_is_the_default_backend(self):
        settings = load_database_settings({})

        self.assertEqual(settings["backend"], "sqlite")
        self.assertIsNone(settings["database_url"])

    def test_explicit_sqlite_does_not_require_database_url(self):
        settings = load_database_settings(
            {"DATABASE_BACKEND": " SQLITE "}
        )

        self.assertEqual(settings["backend"], "sqlite")
        self.assertIsNone(settings["database_url"])

    def test_postgresql_requires_database_url(self):
        with self.assertRaises(ValueError):
            load_database_settings(
                {"DATABASE_BACKEND": "postgresql"}
            )

    def test_postgresql_accepts_valid_connection_url(self):
        database_url = (
            "postgresql://abap_user:password@localhost:5432/abap"
        )

        settings = load_database_settings(
            {
                "DATABASE_BACKEND": "postgresql",
                "DATABASE_URL": database_url,
            }
        )

        self.assertEqual(settings["backend"], "postgresql")
        self.assertEqual(
            settings["database_url"],
            database_url,
        )

    def test_invalid_backend_is_rejected(self):
        with self.assertRaises(ValueError):
            load_database_settings(
                {"DATABASE_BACKEND": "unknown"}
            )

    def test_non_postgresql_url_is_rejected(self):
        with self.assertRaises(ValueError):
            load_database_settings(
                {
                    "DATABASE_BACKEND": "postgresql",
                    "DATABASE_URL": "https://localhost/abap",
                }
            )


if __name__ == "__main__":
    unittest.main()