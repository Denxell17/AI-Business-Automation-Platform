import unittest

from database_sql import adapt_parameter_placeholders


class TestDatabaseSql(unittest.TestCase):
    def test_sqlite_query_is_unchanged(self):
        query = "SELECT * FROM employees WHERE employee_id = ?"

        self.assertEqual(
            adapt_parameter_placeholders(query, "sqlite"),
            query,
        )

    def test_postgresql_uses_percent_s_placeholders(self):
        query = "SELECT * FROM employees WHERE employee_id = ?"

        self.assertEqual(
            adapt_parameter_placeholders(query, "postgresql"),
            "SELECT * FROM employees WHERE employee_id = %s",
        )

    def test_postgresql_adapts_sqlite_specific_queries(self):
        occurrence_query = (
            "INSERT OR IGNORE INTO occurrences (id) "
            "SELECT ?"
        )
        user_query = (
            "SELECT * FROM users WHERE username = ? "
            "ORDER BY username COLLATE NOCASE"
        )

        adapted_occurrence_query = adapt_parameter_placeholders(
            occurrence_query,
            "postgresql",
        )
        adapted_user_query = adapt_parameter_placeholders(
            user_query,
            "postgresql",
        )

        self.assertIn("INSERT INTO occurrences", adapted_occurrence_query)
        self.assertIn("ON CONFLICT DO NOTHING", adapted_occurrence_query)
        self.assertIn(
            "WHERE LOWER(username) = LOWER(%s)",
            adapted_user_query,
        )
        self.assertIn("ORDER BY LOWER(username)", adapted_user_query)

    def test_unknown_backend_is_rejected(self):
        with self.assertRaises(ValueError):
            adapt_parameter_placeholders("SELECT 1", "unknown")


if __name__ == "__main__":
    unittest.main()
